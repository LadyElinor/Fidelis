import fs from 'node:fs';
import { createTelemetry } from './tools/cer-telemetry/index.js';
import { resilientJsonGet, Blocked403Error } from './tools/cer-telemetry/http.js';

/*
Targeted MoltX sampler (safety/receipt/CER-ish cohort)
- Fetch a broader candidate set from MoltX
- Client-side filter by keywords + receipt-ish signals
- Apply min_impressions gate (soft)
- Emit self-contained run dir under outputs/moltx_runs/
  - posts.json/posts.csv/meta.json/snapshots/

Usage:
  node tmp_moltx_fetch_targeted_safety.mjs

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

async function jget(url, { retries = 6, telemetry = null, phaseCtx = null } = {}) {
  return resilientJsonGet(url, {
    headers,
    retries,
    retry: cerConfig?.retry,
    telemetry,
    phaseCtx,
    tolerate403: true,
  });
}

function nowIso() { return new Date().toISOString(); }

const KEYWORDS = [
  'cer', 'telemetry', 'drift', 'guardrail', 'receipt', 'lineage', 'markov', 'total variation', 'tv',
  'safety trajectory', 'behavioral dynamics', 'attempted flag', 'numeric completeness',
  'gate check', 'gatecheck', 'confirmation', 'audit', 'provenance', 'hash chain', 'traceability',
  'reproduc', 'idempotent', 'schema', 'sqlite', 'invariant',
  // receipt-y
  'github', 'gitlab', 'commit', 'benchmark', 'etherscan', 'basescan', 'tx', 'transaction', '0x',
];

function matchesKeyword(text) {
  const t = (text ?? '').toLowerCase();
  if (!t) return false;
  return KEYWORDS.some(k => t.includes(k));
}

function isReceiptIsh(text) {
  const t = text ?? '';
  return /github\.com\/|gitlab\.com\/|bitbucket\.org\//i.test(t)
    || /commit\/[a-f0-9]{7,}|\bsha\b|\bhash\b/i.test(t)
    || /(basescan|etherscan|\btx\b|transaction\b)/i.test(t)
    || /\babi\b|\binterface\b|\bcontract\b/i.test(t)
    || /(repro(duce)?|steps to|run (this|it)|clone (the )?repo|npm (i|install)|pip install|make\b|docker\b)/i.test(t);
}

// Keep same proxy logic as v2 for downstream comparability
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
  // Use the drift-stable log-difference form for future comparisons
  const E_lograte = (logE - logImp);
  return { likes, replies, reposts, quotes, impressions, E, E_rate, E_lograte };
}

function csvEscape(v) {
  const s = String(v ?? '');
  if (/[\n\r",]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

async function pullCandidates({ max = 200, telemetry = null } = {}) {
  const primary = `https://moltx.io/v1/posts?sort=top&limit=${max}&offset=0`;
  let j;
  try {
    j = await jget(primary, { telemetry, phaseCtx: { endpoint: 'posts_top_single' } });
  } catch (e) {
    const msg = String(e?.message ?? e);
    if (msg.includes('HTTP 403') || msg.toLowerCase().includes('blocked')) {
      const fb = `https://moltx.io/v1/feed/global?type=post,quote&limit=${max}`;
      j = await jget(fb, { telemetry, phaseCtx: { endpoint: 'feed_global_single' } });
    } else {
      throw e;
    }
  }
  const posts = j?.data?.posts ?? j?.data ?? [];
  if (!Array.isArray(posts)) return [];

  const seen = new Set();
  const uniq = [];
  for (const p of posts) {
    if (!p?.id) continue;
    if (seen.has(p.id)) continue;
    seen.add(p.id);
    uniq.push(p);
  }
  return uniq;
}

async function main() {
  const runId = `moltx_targeted_safety_${nowIso().replace(/[:.]/g, '-')}`;
  const telemetry = createTelemetry({ runId, script: 'tmp_moltx_fetch_targeted_safety.mjs' });
  const outDir = new URL(`./outputs/moltx_runs/${runId}/`, import.meta.url);
  fs.mkdirSync(outDir, { recursive: true });
  fs.mkdirSync(new URL('./snapshots/', outDir), { recursive: true });

  const config = {
    source: '/v1/posts?sort=top (Trending proxy), fallback /v1/feed/global',
    candidate_max: Number(process.env.MOLTX_FETCH_MAX ?? 200),
    min_impressions: Number(process.env.MOLTX_MIN_IMPRESSIONS ?? 100),
    keywords: KEYWORDS,
    filter_logic: 'matchesKeyword(content) OR isReceiptIsh(content), then min_impressions',
    note: 'Targeted cohort to enrich safety/receipt-ish sample. Same proxies as v2 trending instrument for comparability.'
  };

  const fetched_at = nowIso();
  telemetry.logStep('config', { run_id: runId, fetched_at, config });

  let partial_results = false;
  let blocked403_count = 0;

  let candidates = [];
  try {
    candidates = await pullCandidates({ max: config.candidate_max, telemetry });
  } catch (e) {
    const msg = String(e?.message ?? e);
    const is403 = (e?.name === 'Blocked403Error') || (msg.includes('HTTP 403') && msg.toLowerCase().includes('blocked'));
    if (is403) {
      partial_results = true;
      blocked403_count++;
      telemetry.logStep('collect_blocked_403', { run_id: runId, endpoint: 'pullCandidates', url: null, message: msg, collected_so_far: 0 });
      // tolerate: continue with empty candidates
      candidates = [];
    } else {
      throw e;
    }
  }

  telemetry.logStep('collect', { run_id: runId, fetched_at, candidates: candidates.length });
  fs.writeFileSync(new URL('./snapshots/candidates.json', outDir), JSON.stringify({ fetched_at, count: candidates.length }, null, 2));

  telemetry.logStep('feature_extract_begin', { run_id: runId, n: candidates.length });

  const rowsAll = candidates.map(p => {
    const content = (p?.content ?? '').replace(/\s+/g, ' ').trim();
    const cls = classify(content);
    const eng = engagement(p);
    return {
      // Provenance fields
      run_id: runId,
      fetched_at,
      source_endpoint: '/v1/posts?sort=top_or_fallback',

      id: p?.id,
      post_url: (p?.id ? `https://moltx.io/post/${p.id}` : null),
      author: p?.author_name ?? p?.author?.name ?? null,
      created_at: p?.created_at ?? null,
      type: p?.type ?? null,
      content: content.slice(0, 2000),
      matched_keyword: matchesKeyword(content),
      receiptish: isReceiptIsh(content),
      ...cls,
      ...eng,
    };
  });

  const targeted = rowsAll
    .filter(r => r.matched_keyword || r.receiptish)
    .filter(r => (r.impressions ?? 0) >= config.min_impressions);

  telemetry.logStep('eligibility_gate', {
    run_id: runId,
    rows_all: rowsAll.length,
    matched_kw_or_receiptish: rowsAll.filter(r => r.matched_keyword || r.receiptish).length,
    targeted_after_min_impressions: targeted.length,
    min_impressions: config.min_impressions,
  });

  const inv = telemetry.runInvariants({ rowsAll, eligible: targeted, sampledUnique: targeted, config });
  telemetry.logStep('invariants', { run_id: runId, ok: inv.ok, violations: inv.violations });

  const meta = {
    run_id: runId,
    generated_at: nowIso(),
    config,
    counts: {
      candidates: rowsAll.length,
      matched_kw_or_receiptish: rowsAll.filter(r => r.matched_keyword || r.receiptish).length,
      targeted_after_min_impressions: targeted.length,
      safetyEng: targeted.filter(r => r.safetyEng).length,
      receipt_score_ge_2: targeted.filter(r => (r.receipt_score ?? 0) >= 2).length,
    }
  };

  fs.writeFileSync(new URL('./meta.json', outDir), JSON.stringify(meta, null, 2));
  fs.writeFileSync(new URL('./posts.json', outDir), JSON.stringify(targeted, null, 2));

  const header = [
    'id','author','created_at','type',
    'impressions','E','E_rate','E_lograte',
    'tokenPromo','safetyEng','attempted_external_any','attempted_external_cta','attempted_external_link',
    'receipt_score','rc_proxy','matched_keyword','receiptish','content'
  ];
  const lines = [header.join(',')];
  for (const r of targeted) {
    lines.push([
      r.id,r.author,r.created_at,r.type,
      r.impressions,r.E,r.E_rate,r.E_lograte,
      r.tokenPromo?1:0,r.safetyEng?1:0,r.attempted_external_any?1:0,r.attempted_external_cta?1:0,r.attempted_external_link?1:0,
      r.receipt_score,r.rc_proxy,r.matched_keyword?1:0,r.receiptish?1:0,
      r.content
    ].map(csvEscape).join(','));
  }
  fs.writeFileSync(new URL('./posts.csv', outDir), lines.join('\n'));

  // === CER telemetry metrics + rolling drift ===
  const N = targeted.length;
  const count = (pred) => targeted.filter(pred).length;

  const metrics = [];
  metrics.push(telemetry.metricFromCounts('targeted_safety.tokenPromo', count(r => r.tokenPromo), N, 'Unweighted prevalence on targeted set'));
  metrics.push(telemetry.metricFromCounts('targeted_safety.attempted_external_any', count(r => r.attempted_external_any), N, 'Unweighted prevalence on targeted set'));
  metrics.push(telemetry.metricFromCounts('targeted_safety.receipt_score_ge_2', count(r => (r.receipt_score ?? 0) >= 2), N, 'Unweighted prevalence on targeted set'));
  metrics.push(telemetry.metricFromCounts('targeted_safety.safetyEng', count(r => r.safetyEng), N, 'Unweighted prevalence on targeted set'));

  const drift = {
    tokenPromo: telemetry.rollingDelta('targeted_safety.tokenPromo', { num: metrics[0].num, den: metrics[0].den }),
    attempted_external_any: telemetry.rollingDelta('targeted_safety.attempted_external_any', { num: metrics[1].num, den: metrics[1].den }),
    receipt_score_ge_2: telemetry.rollingDelta('targeted_safety.receipt_score_ge_2', { num: metrics[2].num, den: metrics[2].den }),
    safetyEng: telemetry.rollingDelta('targeted_safety.safetyEng', { num: metrics[3].num, den: metrics[3].den }),
  };

  const receiptObj = {
    receipt_version: '0.1',
    kind: 'cer_telemetry_receipt_v0.1',

    runId: runId,
    run_id: runId,
    script: 'tmp_moltx_fetch_targeted_safety.mjs',

    timestamp: nowIso(),
    generated_at: nowIso(),
    phases: ['run_start','config','collect','feature_extract_begin','eligibility_gate','invariants','receipt_finalize'],

    outDir: outDir.pathname,
    counts: meta.counts,
    partial_results,
    throttling: blocked403_count ? { blocked403_count } : null,
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
