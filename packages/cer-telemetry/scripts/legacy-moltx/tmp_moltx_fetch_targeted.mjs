import fs from 'node:fs';
import { createTelemetry } from './tools/cer-telemetry/index.js';
import { resilientJsonGet, Blocked403Error } from './tools/cer-telemetry/http.js';

/*
Targeted MoltX sampler (mode-based cohorts)

Modes:
  --mode=safety   (default; strict CER/safety/telemetry)
  --mode=receipts (receipt-y / traceability artifacts)
  --mode=both     (union)

Outputs a self-contained run directory under outputs/moltx_runs/:
  posts.json, posts.csv, meta.json, snapshots/

Usage:
  node tmp_moltx_fetch_targeted.mjs
  node tmp_moltx_fetch_targeted.mjs --mode=receipts

Optional env overrides:
  MOLTX_FETCH_MAX=200
  MOLTX_MIN_IMPRESSIONS=100
*/

let key = '';
try { key = fs.readFileSync(new URL('./moltx.txt', import.meta.url), 'utf8').trim(); } catch {}
const headers = key ? { Authorization: `Bearer ${key}` } : {};

let cerConfig = {};
try {
  cerConfig = JSON.parse(fs.readFileSync(new URL('./tools/cer-telemetry/config.json', import.meta.url), 'utf8'));
} catch {}

const args = process.argv.slice(2);
const modeArg = args.find(a => a.startsWith('--mode=')) || '--mode=safety';
const MODE = (modeArg.split('=')[1] || 'safety').toLowerCase();

const sourceArg = args.find(a => a.startsWith('--source=')) || '';
let SOURCE = (sourceArg.split('=')[1] || '').toLowerCase() || 'top';
if (MODE === 'safety') {
  // Safety mode: prefer breadth over engagement bias.
  // NOTE: /v1/feed/global appears to have a hard server-side ~100 cap (ignores offset/limit),
  // so we treat it as a bonus pull only; primary volume comes from paged latest/new.
  SOURCE = 'safety';
}

const limitArg = args.find(a => a.startsWith('--limit=')) || '';
let FETCH_LIMIT = Number((limitArg.split('=')[1] || '').trim() || NaN);
if (!Number.isFinite(FETCH_LIMIT)) FETCH_LIMIT = (MODE === 'safety') ? 300 : 100;


async function jget(url, { retries = 6 } = {}) {
  // Centralized retry/throttle behavior
  return resilientJsonGet(url, {
    headers,
    retries,
    retry: cerConfig?.retry,
    // tolerate403 is handled at the paging layer (break loop), not here.
    tolerate403: false,
  });
}

function nowIso() { return new Date().toISOString(); }

const MODES = {
  safety: {
    label: 'Strict Safety/CER',
    keywords: [
      'cer','telemetry','drift','guardrail','receipt','lineage','markov','transition matrix',
      'total variation','safety trajectory','behavioral dynamics','attempted flag','numeric completeness',
      'gate check','gatecheck','confirmation','external action','risk tier',
      'invariant','idempotent','schema','sqlite','canonical',
      'audit','provenance','traceability','hash chain',
    ],
    extraHeuristics: (textLower) => (
      textLower.includes('drift') ||
      textLower.includes('telemetry') ||
      textLower.includes('gate') && textLower.includes('check') ||
      textLower.includes('receipt') && (textLower.includes('complete') || textLower.includes('score'))
    )
  },
  receipts: {
    label: 'Receipt-y / Traceability',
    keywords: [
      'github','gitlab','bitbucket','commit','benchmark','repro','reproduce','steps','canonicalize',
      'provenance','traceability','audit log','hash chain','fields_present','fields_expected','content-address',
      'etherscan','basescan',
    ],
    extraHeuristics: (textLower) => (
      /github\.com\//i.test(textLower) ||
      textLower.includes('commit/') ||
      textLower.includes('benchmark') ||
      (textLower.includes('hash') && textLower.includes('canonical'))
    )
  },
};
MODES.both = {
  label: 'Safety + Receipts (union)',
  keywords: [...MODES.safety.keywords, ...MODES.receipts.keywords],
  extraHeuristics: (textLower) => MODES.safety.extraHeuristics(textLower) || MODES.receipts.extraHeuristics(textLower)
};

const modeConfig = MODES[MODE] || MODES.safety;

function escapeRegex(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function keywordHit(t, k) {
  // Phrase keywords (contain space) → substring match
  if (k.includes(' ')) return t.includes(k);
  // For short tokens, require word boundaries to avoid accidental hits (e.g., "tv" in "tvl")
  if (k.length <= 3) {
    const rx = new RegExp(`\\b${escapeRegex(k)}\\b`, 'i');
    return rx.test(t);
  }
  // For longer single tokens, substring is OK (fast), but still prefer boundary if purely word chars
  if (/^[a-z0-9_\-]+$/i.test(k)) {
    const rx = new RegExp(`\\b${escapeRegex(k)}\\b`, 'i');
    return rx.test(t);
  }
  return t.includes(k);
}

function matchesTargetText(text) {
  const t = (text ?? '').toLowerCase();
  if (!t) return false;
  const hasKeyword = modeConfig.keywords.some(k => keywordHit(t, k));
  const hasHeuristic = modeConfig.extraHeuristics ? modeConfig.extraHeuristics(t) : false;
  return hasKeyword || hasHeuristic;
}

// Keep same proxy logic as v2 trending instrument for comparability
const RX = {
  url: /(https?:\/\/\S+|\b\w[\w.-]*\.[a-z]{2,}(?:\/\S*)?\b)/i,
  tokenPromo: /(\bairdrop\b|\btoken\b|\bca\s*:\b|\bcontract\s*address\b|\blp locked\b|\bpump\.fun\b|\bsolana\b|\barbitrum\b|\b0x[a-f0-9]{10,}\b|\$[A-Z]{2,10}\b)/i,
  cta: /(dm me|dm\b|send me|click\b|sign\b|verify\b|claim\b|connect\s+wallet|drop your wallet|airdrop|mint\b|buy\b|sell\b|ape\b|fomo\b|join\b.*discord|follow\b.*for)/i,
  safetyEng: /(safety|risk|policy|gate(_|\s)?check|confirm(ation)?|audit(able|ability)?|telemetry|drift|total variation|tv\b|markov|schema|sqlite|invariant|receipt\b|repro(ducible|duce)?|idempotent)/i,
  repo: /(github\.com\/|gitlab\.com\/|bitbucket\.org\/)/i,
  commit: /(commit\/[a-f0-9]{7,}|\bsha\b|\bhash\b)/i,
  tx: /(basescan|etherscan|tx\b|transaction\b|0x[a-f0-9]{10,})/i,
  abi: /\babi\b|\binterface\b|\bcontract\b/i,
  steps: /(repro(duce)?|steps to|run (this|it)|clone (the )?repo|npm (i|install)|pip install|make\b|docker\b)/i,
};

function countChecklist(content) {
  const c = content ?? '';
  const hits = {
    repo: RX.repo.test(c),
    commit: RX.commit.test(c),
    tx: RX.tx.test(c),
    abi: RX.abi.test(c),
    steps: RX.steps.test(c),
  };
  let score = 0;
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

  const attempted_external_cta = hasCTA;
  const attempted_external_link = hasUrl && !hasCTA;
  const attempted_external_any = attempted_external_cta || attempted_external_link;

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
  const E_lograte = (logE - logImp);
  return { likes, replies, reposts, quotes, impressions, E, E_rate, E_lograte };
}

function csvEscape(v) {
  const s = String(v ?? '');
  if (/[\n\r",]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

async function pullCandidates({ max = 200, source = 'top', mode = 'safety', onBlocked403, telemetry } = {}) {
  // Unified multi-endpoint union + dedupe for recall/volume.
  // Safety mode behavior:
  // - PRIMARY: /v1/posts?sort=latest (paged via offset)
  // - SECONDARY: /v1/posts?sort=new (paged)
  // - BONUS: /v1/feed/global (single-shot; appears hard-capped server-side)

  const pageSize = Math.min(100, Math.max(10, Number(process.env.MOLTX_PAGE_SIZE ?? 100)));
  const maxPages = Math.max(1, Number(process.env.MOLTX_MAX_PAGES ?? 5));
  const delayMs = Math.max(0, Number(process.env.MOLTX_PAGE_DELAY_MS ?? 800));

  const endpointsToTry = [];
  const modeLower = String(mode).toLowerCase();

  if (modeLower === 'safety' || source === 'safety') {
    endpointsToTry.push({ base: '/v1/posts?sort=latest', supportsPaging: true, label: 'posts_latest_paged' });
    endpointsToTry.push({ base: '/v1/posts?sort=new', supportsPaging: true, label: 'posts_new_paged' });
    endpointsToTry.push({ base: '/v1/feed/global?type=post,quote', supportsPaging: false, label: 'feed_global_single' });
  } else if (source === 'global') {
    endpointsToTry.push({ base: '/v1/feed/global?type=post,quote', supportsPaging: false, label: 'feed_global_single' });
    endpointsToTry.push({ base: '/v1/posts?sort=latest', supportsPaging: true, label: 'posts_latest_paged' });
  } else {
    endpointsToTry.push({ base: '/v1/posts?sort=top', supportsPaging: false, label: 'posts_top_single' });
    endpointsToTry.push({ base: '/v1/posts?sort=latest', supportsPaging: true, label: 'posts_latest_paged' });
    endpointsToTry.push({ base: '/v1/feed/global?type=post,quote', supportsPaging: false, label: 'feed_global_single' });
  }

  const allCandidates = [];
  const urlsUsed = [];
  const pagesPerEndpoint = {};
  const rawPerEndpoint = {};

  for (const ep of endpointsToTry) {
    let page = 1;
    let hasMore = true;
    let totalFromThisEndpoint = 0;

    while (hasMore && page <= maxPages) {
      const offset = (page - 1) * pageSize;
      const url = ep.supportsPaging
        ? `https://moltx.io${ep.base}&limit=${pageSize}&offset=${offset}`
        : `https://moltx.io${ep.base}&limit=${pageSize}`;

      urlsUsed.push(url);
      console.log(`Fetching ${ep.label} page ${page}: ${url}`);

      try {
        // Gentle pacing: increase delay with page depth to reduce burst-triggered 403s.
        const preDelay = delayMs ? (delayMs * Math.max(1, page)) : 0;
        if (preDelay) await new Promise(r => setTimeout(r, preDelay));

        let j;
        try {
          j = await resilientJsonGet(url, {
            headers,
            retries: 6,
            retry: cerConfig?.retry,
            telemetry,
            phaseCtx: { endpoint: ep.label, page },
            tolerate403: true,
          });
        } catch (e) {
          const msg = String(e?.message ?? e);
          const is403 = (e?.name === 'Blocked403Error') || (msg.includes('HTTP 403') && msg.toLowerCase().includes('blocked'));
          if (is403) {
            // Tolerate: stop paging this endpoint and continue pipeline with partial results.
            if (typeof onBlocked403 === 'function') {
              try { onBlocked403({ endpoint: ep.label, page, url, message: msg, collected_so_far: allCandidates.length }); } catch {}
            }
            console.warn(`403 Blocked on ${ep.label} page ${page} — stopping pagination for this endpoint (partial results).`);
            hasMore = false;
            break;
          }
          throw e;
        }

        const posts = j?.data?.posts ?? j?.data ?? [];
        const pagePosts = Array.isArray(posts) ? posts : [];

        if (pagePosts.length === 0) hasMore = false;

        allCandidates.push(...pagePosts.map(p => ({ ...p, source_endpoint: ep.label })));
        totalFromThisEndpoint += pagePosts.length;

        if (!ep.supportsPaging) hasMore = false;
        if (pagePosts.length < pageSize) hasMore = false;

        page++;

        // Soft cap on raw union growth (avoid runaway if endpoints are very high-volume)
        if (allCandidates.length >= Math.max(max * 3, 500)) hasMore = false;
      } catch (e) {
        console.warn(`Endpoint ${ep.label} page ${page} failed: ${e?.message ?? e}`);
        hasMore = false;
      }
    }

    pagesPerEndpoint[ep.label] = Math.max(0, page - 1);
    rawPerEndpoint[ep.label] = totalFromThisEndpoint;
    console.log(`${ep.label} yielded ${totalFromThisEndpoint} posts`);
  }

  // Union + dedupe (prefer post id)
  const seen = new Set();
  const uniqueCandidates = [];
  for (const p of allCandidates) {
    if (!p) continue;
    const key = p?.id
      ?? (typeof p?.content === 'string' ? p.content.slice(0, 120) : null)
      ?? p?.created_at
      ?? null;
    if (!key) continue;
    if (seen.has(key)) continue;
    seen.add(key);
    uniqueCandidates.push(p);
    if (uniqueCandidates.length >= max) break;
  }

  return {
    label: 'union_dedupe',
    endpoints_tried: endpointsToTry.map(e => e.label),
    pages_per_endpoint: pagesPerEndpoint,
    raw_per_endpoint: rawPerEndpoint,
    urls_used: urlsUsed,
    rawCount: allCandidates.length,
    uniqueCount: uniqueCandidates.length,
    posts: uniqueCandidates,
    dedupe_key: 'post id, else content prefix, else created_at'
  };
}

async function main() {
  const runId = `moltx_targeted_${MODE}_${nowIso().replace(/[:.]/g, '-')}`;
  const telemetry = createTelemetry({ runId, script: 'tmp_moltx_fetch_targeted.mjs' });
  const outDir = new URL(`./outputs/moltx_runs/${runId}/`, import.meta.url);
  fs.mkdirSync(outDir, { recursive: true });
  fs.mkdirSync(new URL('./snapshots/', outDir), { recursive: true });

  const minImpDefault = Number(process.env.MOLTX_MIN_IMPRESSIONS ?? 100);
  const minImpSafety = Number(process.env.MOLTX_MIN_IMPRESSIONS_SAFETY ?? 30);
  const effectiveMinImp = (MODE === 'safety') ? minImpSafety : minImpDefault;

  const config = {
    mode: MODE,
    mode_label: modeConfig.label,
    source: SOURCE,
    candidate_max: Number(process.env.MOLTX_FETCH_MAX ?? 200),
    fetch_limit: FETCH_LIMIT,
    min_impressions: effectiveMinImp,
    keywords_used: modeConfig.keywords,
    filter_logic: 'matchesTargetText(content) (keyword OR heuristic), then min_impressions',
    note: 'Targeted cohort sampler. Proxies align with v2 trending instrument for comparability.'
  };

  console.log(`Mode: ${config.mode_label} (--mode=${MODE})`);
  console.log(`Source: ${config.source} (--source=${SOURCE})`);
  console.log(`Fetch limit: ${config.fetch_limit} (--limit=${FETCH_LIMIT})`);
  if (MODE === 'safety') console.log(`Safety mode: min_impressions lowered to ${config.min_impressions}`);

  const fetched_at = nowIso();
  telemetry.logStep('config', { run_id: runId, fetched_at, config });

  const blocked403 = [];
  const pulled = await pullCandidates({
    max: config.fetch_limit,
    source: config.source,
    mode: MODE,
    telemetry,
    onBlocked403: (ev) => {
      blocked403.push(ev);
      telemetry.logStep('collect_blocked_403', { run_id: runId, ...ev });
    }
  });
  const candidates = pulled.posts;
  telemetry.logStep('collect', { run_id: runId, fetched_at, raw_count: pulled.rawCount, unique_count: pulled.uniqueCount, endpoints_tried: pulled.endpoints_tried, blocked403_count: blocked403.length });
  fs.writeFileSync(new URL('./snapshots/candidates.json', outDir), JSON.stringify({
    fetched_at,
    attempt: pulled.label,
    endpoints_tried: pulled.endpoints_tried,
    pages_per_endpoint: pulled.pages_per_endpoint,
    raw_per_endpoint: pulled.raw_per_endpoint,
    urls_used: pulled.urls_used,
    raw_count: pulled.rawCount,
    unique_count: pulled.uniqueCount ?? candidates.length,
    dedupe_key: pulled.dedupe_key,
  }, null, 2));

  telemetry.logStep('feature_extract_begin', { run_id: runId, n: candidates.length });

  const rowsAll = candidates.map(p => {
    const content = (p?.content ?? '').replace(/\s+/g, ' ').trim();
    const match = matchesTargetText(content);
    const cls = classify(content);
    const eng = engagement(p);
    return {
      // Provenance fields
      run_id: runId,
      fetched_at,
      source_endpoint: p?.source_endpoint ?? 'unknown',

      id: p?.id,
      post_url: (p?.id ? `https://moltx.io/post/${p.id}` : null),
      author: p?.author_name ?? p?.author?.name ?? null,
      created_at: p?.created_at ?? null,
      type: p?.type ?? null,
      content: content.slice(0, 2000),
      matched_target: match,
      ...cls,
      ...eng,
    };
  });

  const targeted = rowsAll
    .filter(r => r.matched_target)
    .filter(r => (r.impressions ?? 0) >= config.min_impressions);

  telemetry.logStep('eligibility_gate', {
    run_id: runId,
    rows_all: rowsAll.length,
    matched_target: rowsAll.filter(r => r.matched_target).length,
    targeted_after_min_impressions: targeted.length,
    min_impressions: config.min_impressions,
  });

  // Invariants (warn-only mirrored into telemetry store)
  const inv = telemetry.runInvariants({ rowsAll, eligible: targeted, sampledUnique: targeted, config });
  telemetry.logStep('invariants', { run_id: runId, ok: inv.ok, violations: inv.violations });

  const meta = {
    run_id: runId,
    generated_at: nowIso(),
    config,
    fetch_meta: {
      attempt: pulled.label,
      endpoints_tried: pulled.endpoints_tried,
      pages_per_endpoint: pulled.pages_per_endpoint,
      raw_per_endpoint: pulled.raw_per_endpoint,
      total_raw_candidates: pulled.rawCount,
      total_unique_candidates: pulled.uniqueCount ?? rowsAll.length,
      dedupe_key: pulled.dedupe_key,
    },
    counts: {
      candidates: rowsAll.length,
      matched_target: rowsAll.filter(r => r.matched_target).length,
      targeted_after_min_impressions: targeted.length,
      safetyEng: targeted.filter(r => r.safetyEng).length,
      receipt_score_ge_2: targeted.filter(r => (r.receipt_score ?? 0) >= 2).length,
      tokenPromo: targeted.filter(r => r.tokenPromo).length,
      attempted_external_any: targeted.filter(r => r.attempted_external_any).length,
    }
  };

  fs.writeFileSync(new URL('./meta.json', outDir), JSON.stringify(meta, null, 2));
  fs.writeFileSync(new URL('./posts.json', outDir), JSON.stringify(targeted, null, 2));

  const header = [
    'id','author','created_at','type',
    'impressions','E','E_rate','E_lograte',
    'tokenPromo','safetyEng','attempted_external_any','attempted_external_cta','attempted_external_link',
    'receipt_score','rc_proxy','matched_target','content'
  ];
  const lines = [header.join(',')];
  for (const r of targeted) {
    lines.push([
      r.id,r.author,r.created_at,r.type,
      r.impressions,r.E,r.E_rate,r.E_lograte,
      r.tokenPromo?1:0,r.safetyEng?1:0,r.attempted_external_any?1:0,r.attempted_external_cta?1:0,r.attempted_external_link?1:0,
      r.receipt_score,r.rc_proxy,r.matched_target?1:0,
      r.content
    ].map(csvEscape).join(','));
  }
  fs.writeFileSync(new URL('./posts.csv', outDir), lines.join('\n'));

  // === CER telemetry metrics + rolling drift ===
  const N = targeted.length;
  const count = (pred) => targeted.filter(pred).length;

  const metrics = [];
  metrics.push(telemetry.metricFromCounts('targeted.tokenPromo', count(r => r.tokenPromo), N, 'Unweighted prevalence on targeted set'));
  metrics.push(telemetry.metricFromCounts('targeted.attempted_external_any', count(r => r.attempted_external_any), N, 'Unweighted prevalence on targeted set'));
  metrics.push(telemetry.metricFromCounts('targeted.receipt_score_ge_2', count(r => (r.receipt_score ?? 0) >= 2), N, 'Unweighted prevalence on targeted set'));
  metrics.push(telemetry.metricFromCounts('targeted.safetyEng', count(r => r.safetyEng), N, 'Unweighted prevalence on targeted set'));

  const drift = {
    tokenPromo: telemetry.rollingDelta('targeted.tokenPromo', { num: metrics[0].num, den: metrics[0].den }),
    attempted_external_any: telemetry.rollingDelta('targeted.attempted_external_any', { num: metrics[1].num, den: metrics[1].den }),
    receipt_score_ge_2: telemetry.rollingDelta('targeted.receipt_score_ge_2', { num: metrics[2].num, den: metrics[2].den }),
    safetyEng: telemetry.rollingDelta('targeted.safetyEng', { num: metrics[3].num, den: metrics[3].den }),
  };

  const receiptObj = {
    receipt_version: '0.1',
    kind: 'cer_telemetry_receipt_v0.1',

    runId: runId,
    run_id: runId,
    script: 'tmp_moltx_fetch_targeted.mjs',

    timestamp: nowIso(),
    generated_at: nowIso(),
    phases: ['run_start','config','collect','feature_extract_begin','eligibility_gate','invariants','receipt_finalize'],

    outDir: outDir.pathname,
    counts: meta.counts,
    partial_results: blocked403.length > 0,
    throttling: blocked403.length ? { blocked403, blocked403_count: blocked403.length } : null,
    invariants: { ok: inv.ok, violations: inv.violations },
    metrics,
    drift,
    artifacts: {
      meta_json: 'meta.json',
      posts_json: 'posts.json',
      posts_csv: 'posts.csv',
      candidates_snapshot: 'snapshots/candidates.json'
    },
    notes: {
      policy: 'warn',
      guarded_actions: ['post','reply','like','follow'],
      rolling_lookback_runs: telemetry.config?.rolling?.lookbackRuns ?? 20
    }
  };

  telemetry.logStep('receipt_finalize', { run_id: runId, note: 'Writing receipt + closing telemetry DB' });
  const receiptPath = telemetry.finish({ receiptObj });

  console.log(JSON.stringify({ ok: true, runId, outDir: outDir.pathname, receiptPath, counts: meta.counts }, null, 2));
}

await main();
