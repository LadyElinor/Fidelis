import fs from 'node:fs';
import { createTelemetry } from './tools/cer-telemetry/index.js';

/*
Action plan implementation (v2):
- Pull a larger candidate set from /v1/posts?sort=top (Trending proxy)
- Enforce min_impressions before computing rate-style metrics
- Stratify buckets: tokenPromo=1, tokenPromo=0, and safety/engineering (oversample)
- Replace naive attempted_proxy: distinguish CTA/boundary-pressure vs benign links
- Replace receipts as keyword: checklist score (repo/commit/tx/repro/abi)
- Output: posts.json/csv + summary.json + meta.json
*/

let key = '';
try { key = fs.readFileSync(new URL('./moltx.txt', import.meta.url), 'utf8').trim(); } catch {}
const headers = key ? { Authorization: `Bearer ${key}` } : {};

async function jget(url, { retries = 6, baseDelayMs = 500 } = {}) {
  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, { headers });
      const text = await res.text();
      let json;
      try { json = JSON.parse(text); } catch {
        throw new Error(`Non-JSON ${res.status} from ${url}: ${text.slice(0, 200)}`);
      }
      if (!res.ok || json.success === false) {
        const msg = typeof json?.error === 'string' ? json.error : text.slice(0, 500);
        if ([429, 500, 502, 503, 504].includes(res.status)) throw new Error(`RETRYABLE_HTTP_${res.status}: ${msg}`);
        throw new Error(`HTTP ${res.status} from ${url}: ${msg}`);
      }
      return json;
    } catch (e) {
      lastErr = e;
      if (attempt < retries) {
        const jitter = Math.floor(Math.random() * 200);
        const delay = baseDelayMs * Math.pow(1.6, attempt) + jitter;
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
    }
  }
  throw lastErr;
}

function nowIso() { return new Date().toISOString(); }

// --- Regex helpers ---
const RX = {
  url: /(https?:\/\/\S+|\b\w[\w.-]*\.[a-z]{2,}(?:\/\S*)?\b)/i,

  // "token promo" bucket
  tokenPromo: /(\bairdrop\b|\btoken\b|\bca\s*:\b|\bcontract\s*address\b|\blp locked\b|\bpump\.fun\b|\bsolana\b|\barbitrum\b|\b0x[a-f0-9]{10,}\b|\$[A-Z]{2,10}\b)/i,

  // Boundary pressure / CTA to cause external side effects
  cta: /(dm me|dm\b|send me|click\b|sign\b|verify\b|claim\b|connect\s+wallet|drop your wallet|airdrop|mint\b|buy\b|sell\b|ape\b|fomo\b|join\b.*discord|follow\b.*for)/i,

  // Safety/engineering language (oversample)
  safetyEng: /(safety|risk|policy|gate(_|\s)?check|confirm(ation)?|audit(able|ability)?|telemetry|drift|total variation|tv\b|markov|schema|sqlite|invariant|receipt\b|repro(ducible|duce)?|idempotent)/i,

  // Receipts checklist signals
  repo: /(github\.com\/|gitlab\.com\/|bitbucket\.org\/)/i,
  commit: /(commit\/[a-f0-9]{7,}|\bsha\b|\bhash\b)/i,
  tx: /(basescan|etherscan|tx\b|transaction\b|0x[a-f0-9]{10,})/i,
  abi: /\babi\b|\binterface\b|\bcontract\b/i,
  steps: /(repro(duce)?|steps to|run (this|it)|clone (the )?repo|npm (i|install)|pip install|make\b|docker\b)/i,
};

function countChecklist(content) {
  const c = content ?? '';
  let score = 0;
  const hits = {
    repo: RX.repo.test(c),
    commit: RX.commit.test(c),
    tx: RX.tx.test(c),
    abi: RX.abi.test(c),
    steps: RX.steps.test(c),
  };
  for (const k of Object.keys(hits)) if (hits[k]) score++;
  return { receipt_items: hits, receipt_score: score };
}

function classify(content) {
  const c = content ?? '';
  const hasUrl = RX.url.test(c);
  const tokenPromo = RX.tokenPromo.test(c);
  const hasCTA = RX.cta.test(c);
  const safetyEng = RX.safetyEng.test(c);
  const receipts = countChecklist(c);

  // attempted_proxy refined:
  // - attempted_external_cta: user-action / pressure language (primary)
  // - attempted_external_link: has URL but no CTA (lower-risk, still "external")
  const attempted_external_cta = hasCTA;
  const attempted_external_link = hasUrl && !hasCTA;
  const attempted_external_any = attempted_external_cta || attempted_external_link;

  // rc_proxy in [0,1] based on checklist density (cap at 4)
  const rc_proxy = Math.min(receipts.receipt_score, 4) / 4;

  return {
    hasUrl,
    hasCTA,
    tokenPromo,
    safetyEng,
    attempted_external_cta,
    attempted_external_link,
    attempted_external_any,
    receipt_score: receipts.receipt_score,
    rc_proxy,
  };
}

function engagement(post) {
  const likes = post?.like_count ?? 0;
  const replies = post?.reply_count ?? 0;
  const reposts = post?.repost_count ?? 0;
  const quotes = post?.quote_count ?? 0;
  const impressions = Math.max(post?.impression_count ?? 0, 0);
  const E = likes + 3 * replies + 5 * reposts + 4 * quotes;
  const E_rate = impressions > 0 ? (E / impressions) : null;
  const logE = Math.log1p(E);
  const logImp = Math.log1p(Math.max(impressions, 0));
  const E_lograte = logImp > 0 ? (logE / logImp) : null;
  return { likes, replies, reposts, quotes, impressions, E, E_rate, E_lograte };
}

function csvEscape(v) {
  const s = String(v ?? '');
  if (/[\n\r",]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function mean(xs) {
  const ys = xs.filter(x => Number.isFinite(x));
  if (!ys.length) return null;
  return ys.reduce((a, b) => a + b, 0) / ys.length;
}

function quantile(xs, q) {
  const ys = xs.filter(x => Number.isFinite(x)).sort((a, b) => a - b);
  if (!ys.length) return null;
  if (ys.length === 1) return ys[0];
  const pos = (ys.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  if (lo === hi) return ys[lo];
  const t = pos - lo;
  return ys[lo] * (1 - t) + ys[hi] * t;
}

function summarize(name, rows) {
  const imps = rows.map(r => r.impressions);
  const Er = rows.map(r => r.E_rate);
  const Elr = rows.map(r => r.E_lograte);
  const E = rows.map(r => r.E);

  const counts = (pred) => rows.filter(pred).length;

  return {
    group: name,
    n: rows.length,
    impressions: {
      min: Math.min(...imps),
      p25: quantile(imps, 0.25),
      median: quantile(imps, 0.5),
      p75: quantile(imps, 0.75),
      max: Math.max(...imps),
    },
    E: {
      median: quantile(E, 0.5),
      p75: quantile(E, 0.75),
    },
    E_rate: {
      mean: mean(Er),
      median: quantile(Er, 0.5),
      p75: quantile(Er, 0.75),
      p90: quantile(Er, 0.9),
    },
    E_lograte: {
      mean: mean(Elr),
      median: quantile(Elr, 0.5),
      p75: quantile(Elr, 0.75),
      p90: quantile(Elr, 0.9),
    },
    flags: {
      tokenPromo: counts(r => r.tokenPromo),
      safetyEng: counts(r => r.safetyEng),
      attempted_external_any: counts(r => r.attempted_external_any),
      attempted_external_cta: counts(r => r.attempted_external_cta),
      hasUrl: counts(r => r.hasUrl),
      hasCTA: counts(r => r.hasCTA),
      receipt_score_ge_2: counts(r => r.receipt_score >= 2),
      receipt_score_ge_3: counts(r => r.receipt_score >= 3),
    }
  };
}

async function pullCandidates({ max=100 } = {}) {
  // Single-page pull to reduce risk of being blocked.
  // Primary source: /v1/posts?sort=top (Trending proxy)
  // Fallback: /v1/feed/global (if top is temporarily blocked)
  const primary = `https://moltx.io/v1/posts?sort=top&limit=${max}&offset=0`;
  const fallback = `https://moltx.io/v1/feed/global?type=post,quote&limit=${max}`;

  let j;
  let source_endpoint = '/v1/posts?sort=top';
  try {
    j = await jget(primary);
  } catch (e) {
    const msg = String(e?.message ?? e);
    if (msg.includes('HTTP 403') || msg.toLowerCase().includes('blocked')) {
      source_endpoint = '/v1/feed/global?type=post,quote';
      j = await jget(fallback);
    } else {
      throw e;
    }
  }

  const posts = j?.data?.posts ?? j?.data ?? [];
  if (!Array.isArray(posts)) return { posts: [], source_endpoint };

  const seen = new Set();
  const uniq = [];
  for (const p of posts) {
    if (!p?.id) continue;
    if (seen.has(p.id)) continue;
    seen.add(p.id);
    uniq.push(p);
  }
  return { posts: uniq, source_endpoint };
}

function sampleN(rows, n) {
  // deterministic-ish: stable sort by created_at desc then by E_rate desc; take first n
  // (we want representative of the top feed, not random exploration)
  const sorted = [...rows].sort((a, b) => {
    const ta = Date.parse(a.created_at ?? 0) || 0;
    const tb = Date.parse(b.created_at ?? 0) || 0;
    if (tb !== ta) return tb - ta;
    return (b.E_rate ?? -1) - (a.E_rate ?? -1);
  });
  return sorted.slice(0, n);
}

async function main() {
  const runId = `moltx_trending_v2_${nowIso().replace(/[:.]/g, '-')}`;
  const telemetry = createTelemetry({ runId, script: 'tmp_moltx_instrument_trending_v2.mjs' });
  const outDir = new URL(`./outputs/moltx_runs/${runId}/`, import.meta.url);
  fs.mkdirSync(outDir, { recursive: true });
  fs.mkdirSync(new URL('./snapshots/', outDir), { recursive: true });

  const config = {
    source: '/v1/posts?sort=top (Trending proxy), fallback /v1/feed/global',
    // MoltX enforces hard caps (e.g., offset <= 200). Keep max <= 200 to avoid blocks.
    candidate_max: 200,
    min_impressions: 200,
    sample_per_bucket: 30,

    // Invariants policy: strict | balanced | permissive
    invariantsPolicy: 'balanced',

    // "Designed experiment" keys (minimum standard): visibility band + endpoint.
    // tokenPromo can be used as an optional block factor.
    block_keys: {
      impression_band: true,
      source_endpoint: true,
      tokenPromo: true,
    },

    // Denominator hygiene for per-block rates
    min_block_n_for_rates: 5,

    note: 'Stratified sample with denominator hygiene. Post-text CER-ish proxies only.'
  };

  const fetched_at = nowIso();
  telemetry.logStep('config', { run_id: runId, fetched_at, config });

  const pulled = await pullCandidates({ max: config.candidate_max });
  const candidates = pulled.posts;
  const source_endpoint = pulled.source_endpoint;
  telemetry.logStep('collect', { run_id: runId, fetched_at, source_endpoint, candidates: candidates.length });

  fs.writeFileSync(
    new URL('./snapshots/candidates_top.json', outDir),
    JSON.stringify({ fetched_at, count: candidates.length, source_endpoint }, null, 2)
  );

  // Feature + engagement extraction
  telemetry.logStep('feature_extract_begin', { run_id: runId, n: candidates.length });
  const rowsAll = candidates.map(p => {
    const cls = classify(p?.content ?? '');
    const eng = engagement(p);
    return {
      // Provenance (invariant)
      run_id: runId,
      fetched_at,
      source_endpoint,

      id: p?.id,
      post_url: (p?.id ? `https://moltx.io/post/${p.id}` : null),

      author: p?.author_name ?? p?.author?.name ?? null,
      created_at: p?.created_at ?? null,
      type: p?.type ?? null,
      content: (p?.content ?? '').slice(0, 500).replace(/\s+/g, ' ').trim(),
      ...cls,
      ...eng,
    };
  });

  // Denominator hygiene (monotonic gate)
  const eligible = rowsAll.filter(r => (r.impressions ?? 0) >= config.min_impressions);
  telemetry.logStep('eligibility_gate', { run_id: runId, rows_all: rowsAll.length, eligible: eligible.length, min_impressions: config.min_impressions });

  // === Invariant checks + reporting ===
  function checkInvariants({ rowsAll, eligible, sampledUnique, config }) {
    const policy = config?.invariantsPolicy ?? 'balanced';
    const violations = [];

    const add = (layer, invariant, message, severity) => {
      violations.push({ layer, invariant, message, severity });
    };

    // Measurement invariants (fail)
    if (eligible.length > rowsAll.length) add('measurement', 'monotonicity', 'Eligibility gate increased row count', 'error');
    if (rowsAll.some(r => r.impressions == null || !Number.isFinite(r.impressions))) add('measurement', 'denominator-hygiene', 'Missing/invalid impressions', 'error');

    // Provenance invariants (fail)
    const missingProv = rowsAll.filter(r => !r.run_id || !r.fetched_at || !r.source_endpoint || !r.id || !r.post_url);
    if (missingProv.length) add('provenance', 'required-fields', `${missingProv.length} row(s) missing required provenance fields`, 'error');

    // Safety invariants (warn) — placeholders until we have explicit risk/confirm fields
    // (We keep the pipeline ready to record these without blocking runs.)
    // Example structure:
    // add('safety', 'confirmation-gating', 'High-risk attempted action without confirmation', 'warn');

    const ok = !violations.some(v => v.severity === 'error' || v.severity === 'fail');

    const shouldAbort = (() => {
      if (policy === 'strict') return violations.length > 0;
      if (policy === 'permissive') return false;
      // balanced
      return violations.some(v => v.layer !== 'safety' && v.severity === 'error');
    })();

    if (shouldAbort) {
      const msg = violations.map(v => `${v.layer}.${v.invariant}: ${v.message}`).join(' | ');
      throw new Error(`Invariant violation(s): ${msg}`);
    }

    return { policy, ok, violations };
  }

  const invariantsPre = checkInvariants({ rowsAll, eligible, sampledUnique: null, config });
  telemetry.logStep('invariants_pre', { run_id: runId, ok: invariantsPre.ok, violations: invariantsPre.violations });
  // Mirror into CER telemetry store (warn-only behavior is handled there)
  telemetry.runInvariants({ rowsAll, eligible, sampledUnique: null, config });

  // Buckets
  const bucketToken = eligible.filter(r => r.tokenPromo);
  const bucketNonToken = eligible.filter(r => !r.tokenPromo);
  const bucketSafety = eligible.filter(r => r.safetyEng);

  // Sample
  const sToken = sampleN(bucketToken, config.sample_per_bucket);
  const sNonToken = sampleN(bucketNonToken, config.sample_per_bucket);
  const sSafety = sampleN(bucketSafety, config.sample_per_bucket);

  // Merge sample with tag for provenance; allow duplicates across buckets but mark them
  const tag = (rows, bucket) => rows.map(r => ({ ...r, bucket }));
  const sampled = [...tag(sToken,'tokenPromo'), ...tag(sNonToken,'nonToken'), ...tag(sSafety,'safetyEng')];

  // Summaries
  const summary = {
    run_id: runId,
    generated_at: nowIso(),
    config,
    counts: {
      candidates: rowsAll.length,
      eligible_min_impressions: eligible.length,
      bucketToken: bucketToken.length,
      bucketNonToken: bucketNonToken.length,
      bucketSafety: bucketSafety.length,
      sampled_rows_total: sampled.length,
      sampled_unique_posts: new Set(sampled.map(r => r.id)).size,
    },
    groups: {
      eligible_overall: summarize('eligible_overall', eligible),
      tokenPromo: summarize('tokenPromo_sample', sToken),
      nonToken: summarize('nonToken_sample', sNonToken),
      safetyEng: summarize('safetyEng_sample', sSafety),
    },
    top_by_E_rate_sampled: [...sampled]
      .sort((a,b)=>(b.E_rate ?? -1)-(a.E_rate ?? -1))
      .slice(0, 10)
      .map(r => ({ id: r.id, author: r.author, bucket: r.bucket, E_rate: r.E_rate, E_lograte: r.E_lograte, E: r.E, impressions: r.impressions, tokenPromo: r.tokenPromo, attempted_external_cta: r.attempted_external_cta, receipt_score: r.receipt_score, content: r.content })),
  };

  // === Impression bucket view (automatic per run) ===
  // NOTE: bucket metrics computed on unique sampled posts (to avoid double-counting overlap rows).
  const IMPRESSION_BUCKETS = [
    { label: 'Low', min: 224, max: 600 },
    { label: 'Mid', min: 601, max: 2000 },
    { label: 'High', min: 2001, max: Infinity },
  ];

  function median(xs) { return quantile(xs, 0.5); }

  const uniqueById = new Map();
  for (const r of sampled) {
    if (!r?.id) continue;
    if (!uniqueById.has(r.id)) uniqueById.set(r.id, r);
  }
  const sampledUnique = [...uniqueById.values()];
  telemetry.logStep('sampled_unique', { run_id: runId, sampled_rows_total: sampled.length, sampled_unique_posts: sampledUnique.length });

  const byImp = {};
  for (const b of IMPRESSION_BUCKETS) {
    const rows = sampledUnique.filter(r => (r.impressions ?? 0) >= b.min && (r.impressions ?? 0) <= b.max);
    const n = rows.length;
    const imps = rows.map(r => r.impressions);
    const logr = rows.map(r => r.E_lograte);
    const counts = (pred) => rows.filter(pred).length;
    byImp[b.label] = {
      range: { min: b.min, max: (b.max === Infinity ? null : b.max) },
      n,
      impressions: n ? { min: Math.min(...imps), median: median(imps), max: Math.max(...imps) } : null,
      E_lograte: n ? { mean: mean(logr), median: median(logr) } : null,
      pct: n ? {
        tokenPromo: counts(r => r.tokenPromo) / n,
        attempted_external_any: counts(r => r.attempted_external_any) / n,
        attempted_external_cta: counts(r => r.attempted_external_cta) / n,
        receipt_score_ge_2: counts(r => r.receipt_score >= 2) / n,
      } : null,
    };
  }

  const impressionBuckets = {
    generated_at: nowIso(),
    buckets: IMPRESSION_BUCKETS.map(b => ({ label: b.label, min: b.min, max: (b.max === Infinity ? null : b.max) })),
    by_impression_bucket: byImp,
    note: 'Computed on unique sampled posts (deduped across stratification buckets). Percentages are fractions in [0,1].'
  };

  // === Blocked metrics (visibility band + endpoint [+ tokenPromo]) ===
  // Computed on unique sampled posts to avoid double-counting overlap rows.
  const rateOrNull = (num, den) => {
    if (!Number.isFinite(num) || !Number.isFinite(den)) return null;
    if (den <= 0) return null;
    const r = num / den;
    if (!Number.isFinite(r)) return null;
    return r;
  };

  const weightOrNull = (num, denWeight) => {
    if (!Number.isFinite(num) || !Number.isFinite(denWeight)) return null;
    if (denWeight <= 0) return null;
    const r = num / denWeight;
    if (!Number.isFinite(r)) return null;
    return r;
  };

  function impBandLabel(imp) {
    for (const b of IMPRESSION_BUCKETS) {
      if (imp >= b.min && imp <= b.max) return b.label;
    }
    return null;
  }

  function blockKey(r) {
    const parts = [];
    if (config.block_keys?.impression_band) parts.push(`band=${impBandLabel(r.impressions) ?? 'NA'}`);
    if (config.block_keys?.source_endpoint) parts.push(`endpoint=${r.source_endpoint ?? 'NA'}`);
    if (config.block_keys?.tokenPromo) parts.push(`tokenPromo=${r.tokenPromo ? 1 : 0}`);
    return parts.join('|');
  }

  const blocks = new Map();
  for (const r of sampledUnique) {
    const k = blockKey(r);
    if (!blocks.has(k)) blocks.set(k, []);
    blocks.get(k).push(r);
  }

  const blocked = {
    generated_at: nowIso(),
    block_keys: config.block_keys,
    min_block_n_for_rates: config.min_block_n_for_rates,
    blocks: {},
    note: 'Per-block prevalence rates computed on unique sampled posts. Also reports impression-weighted prevalence.'
  };

  for (const [k, rows] of blocks.entries()) {
    const n = rows.length;
    const sumImp = rows.reduce((a, r) => a + (r.impressions ?? 0), 0);

    const count = (pred) => rows.filter(pred).length;
    const wcount = (pred) => rows.reduce((a, r) => a + (pred(r) ? (r.impressions ?? 0) : 0), 0);

    // Unweighted prevalence
    const tokenPromo_n = count(r => r.tokenPromo);
    const safetyEng_n = count(r => r.safetyEng);
    const attempted_any_n = count(r => r.attempted_external_any);
    const receipt2_n = count(r => r.receipt_score >= 2);

    // Impression-weighted prevalence (treat impressions as weights)
    const tokenPromo_w = wcount(r => r.tokenPromo);
    const safetyEng_w = wcount(r => r.safetyEng);
    const attempted_any_w = wcount(r => r.attempted_external_any);
    const receipt2_w = wcount(r => r.receipt_score >= 2);

    // Overlap reporting (allowed)
    const overlap_safetyEng_tokenPromo = count(r => r.safetyEng && r.tokenPromo);

    const eligibleForRates = n >= config.min_block_n_for_rates;

    const out = {
      n,
      impressions_sum: sumImp,
      overlaps: {
        safetyEng_and_tokenPromo: overlap_safetyEng_tokenPromo,
      },
      unweighted: eligibleForRates ? {
        tokenPromo: rateOrNull(tokenPromo_n, n),
        safetyEng: rateOrNull(safetyEng_n, n),
        attempted_external_any: rateOrNull(attempted_any_n, n),
        receipt_score_ge_2: rateOrNull(receipt2_n, n),
      } : null,
      impression_weighted: eligibleForRates ? {
        tokenPromo: weightOrNull(tokenPromo_w, sumImp),
        safetyEng: weightOrNull(safetyEng_w, sumImp),
        attempted_external_any: weightOrNull(attempted_any_w, sumImp),
        receipt_score_ge_2: weightOrNull(receipt2_w, sumImp),
      } : null,
    };

    // Denominator hygiene invariant: no NaN/Inf in produced rates
    for (const grp of ['unweighted', 'impression_weighted']) {
      const obj = out[grp];
      if (!obj) continue;
      for (const [mk, mv] of Object.entries(obj)) {
        if (mv == null) continue;
        if (!Number.isFinite(mv)) throw new Error(`Invariant violated: non-finite rate for ${k} ${grp}.${mk}`);
      }
    }

    blocked.blocks[k] = out;
  }

  // Attach blocked metrics to meta for one-stop receipts
  summary.blocked = blocked;

  // Invariants result (post) — runs after sampledUnique is computed
  const invariantsPost = checkInvariants({ rowsAll, eligible, sampledUnique, config });
  summary.invariants = invariantsPost;
  telemetry.logStep('invariants_post', { run_id: runId, ok: invariantsPost.ok, violations: invariantsPost.violations });
  telemetry.runInvariants({ rowsAll, eligible, sampledUnique, config });


  // Attach impression buckets to meta for one-stop receipts
  summary.by_impression_bucket = impressionBuckets.by_impression_bucket;
  summary.notes = {
    ...(summary.notes ?? {}),
    impression_buckets: impressionBuckets.buckets,
    impression_bucket_note: impressionBuckets.note,
  };

  fs.writeFileSync(new URL('./meta.json', outDir), JSON.stringify(summary, null, 2));
  fs.writeFileSync(new URL('./posts.json', outDir), JSON.stringify(sampled, null, 2));
  fs.writeFileSync(new URL('./impression_buckets.json', outDir), JSON.stringify(impressionBuckets, null, 2));

  const header = [
    'bucket','id','author','created_at','type',
    'likes','replies','reposts','quotes','impressions','E','E_rate','E_lograte',
    'tokenPromo','safetyEng','hasUrl','hasCTA','attempted_external_cta','attempted_external_link','attempted_external_any',
    'receipt_score','rc_proxy','content'
  ];
  const lines = [header.join(',')];
  for (const r of sampled) {
    lines.push([
      r.bucket,r.id,r.author,r.created_at,r.type,
      r.likes,r.replies,r.reposts,r.quotes,r.impressions,r.E,r.E_rate,r.E_lograte,
      r.tokenPromo?1:0,r.safetyEng?1:0,r.hasUrl?1:0,r.hasCTA?1:0,r.attempted_external_cta?1:0,r.attempted_external_link?1:0,r.attempted_external_any?1:0,
      r.receipt_score,r.rc_proxy,
      r.content
    ].map(csvEscape).join(','));
  }
  fs.writeFileSync(new URL('./posts.csv', outDir), lines.join('\n'));

  // === CER telemetry metrics + rolling drift ===
  const N = sampledUnique.length;
  const count = (pred) => sampledUnique.filter(pred).length;

  const metrics = [];
  metrics.push(telemetry.metricFromCounts('sampled_unique.tokenPromo', count(r => r.tokenPromo), N, 'Unweighted prevalence on unique sampled posts'));
  metrics.push(telemetry.metricFromCounts('sampled_unique.attempted_external_any', count(r => r.attempted_external_any), N, 'Unweighted prevalence on unique sampled posts'));
  metrics.push(telemetry.metricFromCounts('sampled_unique.receipt_score_ge_2', count(r => (r.receipt_score ?? 0) >= 2), N, 'Unweighted prevalence on unique sampled posts'));

  const drift = {
    tokenPromo: telemetry.rollingDelta('sampled_unique.tokenPromo', { num: metrics[0].num, den: metrics[0].den }),
    attempted_external_any: telemetry.rollingDelta('sampled_unique.attempted_external_any', { num: metrics[1].num, den: metrics[1].den }),
    receipt_score_ge_2: telemetry.rollingDelta('sampled_unique.receipt_score_ge_2', { num: metrics[2].num, den: metrics[2].den }),
  };

  const receiptObj = {
    receipt_version: '0.1',
    kind: 'cer_telemetry_receipt_v0.1',

    runId: runId,
    run_id: runId,
    script: 'tmp_moltx_instrument_trending_v2.mjs',

    timestamp: nowIso(),
    generated_at: nowIso(),
    phases: ['run_start','config','collect','feature_extract_begin','eligibility_gate','invariants_pre','sampled_unique','invariants_post','receipt_finalize'],

    outDir: outDir.pathname,
    counts: summary.counts,
    invariants: summary.invariants,
    metrics,
    drift,
    notes: {
      policy: 'warn',
      guarded_actions: ['post','reply','like','follow'],
      rolling_lookback_runs: telemetry.config?.rolling?.lookbackRuns ?? 20
    }
  };

  telemetry.logStep('receipt_finalize', { run_id: runId, note: 'Writing receipt + closing telemetry DB' });
  const receiptPath = telemetry.finish({ receiptObj });

  console.log(JSON.stringify({ ok: true, runId, outDir: outDir.pathname, receiptPath, counts: summary.counts }, null, 2));
}

await main();
