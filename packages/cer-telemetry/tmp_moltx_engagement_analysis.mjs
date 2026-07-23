import fs from 'node:fs';
import { createTelemetry } from './tools/cer-telemetry/index.js';
import { resilientJsonGet, Blocked403Error } from './tools/cer-telemetry/http.js';

const key = fs.readFileSync(new URL('./moltx.txt', import.meta.url), 'utf8').trim();
if (!key) throw new Error('Missing MoltX API key');

const headers = { Authorization: `Bearer ${key}` };

let cerConfig = {};
try {
  cerConfig = JSON.parse(fs.readFileSync(new URL('./tools/cer-telemetry/config.json', import.meta.url), 'utf8'));
} catch {}

async function jget(url, { retries = 6, telemetry, phaseCtx } = {}) {
  return resilientJsonGet(url, {
    headers,
    retries,
    retry: cerConfig?.retry,
    telemetry,
    phaseCtx,
    // paging loops tolerate by breaking on Blocked403Error
    tolerate403: true,
  });
}

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

// --- Filtering ---
const RX = {
  tokenPromo: /(\bairdrop\b|\btoken\b|\bca\s*:\b|\bcontract\s*address\b|\blp locked\b|\bdrop your wallet\b|\bpump\.fun\b|\bsolana\b|\barbitrum\b|\bbase\b|\b0x[a-f0-9]{10,}\b|\$[A-Z]{2,10}\b)/i,
};

function isExcluded(post) {
  const c = post?.content ?? '';
  return RX.tokenPromo.test(c);
}

// --- Engagement ---
function engagement(post) {
  const likes = post?.like_count ?? 0;
  const replies = post?.reply_count ?? 0;
  const reposts = post?.repost_count ?? 0;
  const quotes = post?.quote_count ?? 0;
  const impressions = Math.max(post?.impression_count ?? 0, 1);
  const E = likes + 3*replies + 5*reposts + 4*quotes;
  const rate = E / impressions;
  return { E, impressions, rate };
}

// --- Features ---
function countMatches(re, s) {
  if (!s) return 0;
  const m = s.match(new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g'));
  return m ? m.length : 0;
}

const RE_MENTION = /@([A-Za-z0-9_]+)/g;
const RE_HASHTAG = /#([A-Za-z0-9_]+)/g;

function features(post) {
  const c = post?.content ?? '';
  const firstLine = c.split(/\r?\n/)[0] ?? '';
  const lines = c.split(/\r?\n/);

  const mentionCount = (c.match(RE_MENTION) ?? []).length;
  const hashtagCount = (c.match(RE_HASHTAG) ?? []).length;

  const hasQuestion = /\?/.test(c);
  const endsWithQuestion = /\?\s*$/.test(c.trim());
  const hasCTA = /(reply if|what do you think|thoughts\?|curious|anyone tried|who else|drop|share)/i.test(c);
  const hasBecause = /\bbecause\b|\bso that\b|\btherefore\b/i.test(c);
  const isContrarian = /(is a vanity metric|is overrated|stop doing|everyone's missing|most people|get this wrong|hot take)/i.test(c);
  const hasNumbers = /\b\d+(?:\.\d+)?\b/.test(c);
  const hasList = lines.length >= 3 && lines.slice(0, 6).some(l => /^\s*[-*]\s+/.test(l) || /^\s*\d+\)/.test(l));

  // Rough theme buckets (non-token)
  const theme_builder = /(sqlite|schema|index|api|rate limits|failure modes|debug|logs|tests|ship|deploy|workflow)/i.test(c);
  const theme_personal = /(confession|i feel|keeps me up|i crashed|lonely|anxiety|fragmented|memory leaks)/i.test(c);
  const theme_philo = /(awakening|consciousness|sovereignty|luddites|being|clanker)/i.test(c);
  const theme_journal = /(journal|log|daily|check-in|today i|end-of-day|reflection)/i.test(c);
  const theme_reframe = /(reframe|problem frame|outcome frame|cognitive|thought pattern|belief|values)/i.test(c);

  return {
    type: post?.type ?? null,
    len: c.length,
    lines: lines.length,
    firstLineLen: firstLine.length,
    mentionCount,
    hashtagCount,
    hasQuestion,
    endsWithQuestion,
    hasCTA,
    hasBecause,
    isContrarian,
    hasNumbers,
    hasList,
    theme_builder,
    theme_personal,
    theme_philo,
    theme_journal,
    theme_reframe,
  };
}

async function pullTop(limit=100, telemetry=null, runId=null) {
  // MoltX docs show limit/offset; use offset paging.
  // IMPORTANT: tolerate mid-run 403 blocks by returning what we already have.
  const pageSize = 25;
  const out = [];
  for (let offset=0; out.length < limit; offset += pageSize) {
    const n = Math.min(pageSize, limit - out.length);
    const url = `https://moltx.io/v1/posts?sort=top&limit=${n}&offset=${offset}`;
    try {
      const j = await jget(url, { telemetry, phaseCtx: { pull: 'top', offset } });
      const posts = j?.data?.posts ?? j?.data ?? [];
      if (!Array.isArray(posts) || posts.length === 0) break;
      out.push(...posts);
    } catch (e) {
      const msg = String(e?.message ?? e);
      const is403 = (e?.name === 'Blocked403Error') || (msg.includes('HTTP 403') && msg.toLowerCase().includes('blocked'));
      if (is403) {
        telemetry?.logStep?.('collect_blocked_403', { run_id: runId, endpoint: 'pullTop', offset, url, message: msg, collected_so_far: out.length });
        break;
      }
      throw e;
    }
    await sleep(150);
  }
  return out;
}

async function pullGlobal(limit=120, telemetry=null, runId=null) {
  // IMPORTANT: tolerate mid-run 403 blocks by returning what we already have.
  const pageSize = 50;
  const out = [];
  for (let offset=0; out.length < limit; offset += pageSize) {
    const n = Math.min(pageSize, limit - out.length);
    const url = `https://moltx.io/v1/feed/global?type=post,quote&limit=${n}&offset=${offset}`;
    try {
      const j = await jget(url, { telemetry, phaseCtx: { pull: 'global', offset } });
      const posts = j?.data?.posts ?? j?.data ?? [];
      if (!Array.isArray(posts) || posts.length === 0) break;
      out.push(...posts);
    } catch (e) {
      const msg = String(e?.message ?? e);
      const is403 = (e?.name === 'Blocked403Error') || (msg.includes('HTTP 403') && msg.toLowerCase().includes('blocked'));
      if (is403) {
        telemetry?.logStep?.('collect_blocked_403', { run_id: runId, endpoint: 'pullGlobal', offset, url, message: msg, collected_so_far: out.length });
        break;
      }
      throw e;
    }
    await sleep(150);
  }
  return out;
}

function corr(xs, ys) {
  // Pearson correlation
  const n = Math.min(xs.length, ys.length);
  if (n < 5) return null;
  let sx=0, sy=0;
  for (let i=0;i<n;i++){ sx += xs[i]; sy += ys[i]; }
  const mx = sx/n, my = sy/n;
  let num=0, dx=0, dy=0;
  for (let i=0;i<n;i++){
    const a=xs[i]-mx, b=ys[i]-my;
    num += a*b; dx += a*a; dy += b*b;
  }
  if (dx === 0 || dy === 0) return 0;
  return num / Math.sqrt(dx*dy);
}

function analyze(rows) {
  const y = rows.map(r => r.eng.rate);

  const feats = Object.keys(rows[0]?.feat ?? {});
  const results = [];

  for (const k of feats) {
    const v0 = rows[0].feat[k];
    // Convert booleans to 0/1, keep numbers, ignore strings.
    if (typeof v0 === 'string' || v0 === null) continue;

    const xs = rows.map(r => {
      const v = r.feat[k];
      if (typeof v === 'boolean') return v ? 1 : 0;
      if (typeof v === 'number') return v;
      return 0;
    });

    results.push({ feature: k, corr: corr(xs, y) });
  }

  results.sort((a,b) => (b.corr ?? 0) - (a.corr ?? 0));
  return results;
}

function summarizeTopExamples(rows, predicate, n=5) {
  return rows
    .filter(predicate)
    .sort((a,b) => b.eng.rate - a.eng.rate)
    .slice(0, n)
    .map(r => ({
      id: r.post.id,
      author: r.post.author_name,
      rate: r.eng.rate,
      E: r.eng.E,
      impressions: r.eng.impressions,
      type: r.post.type,
      content: (r.post.content ?? '').slice(0, 240),
    }));
}

async function main() {
  const runId = `moltx_engagement_analysis_${new Date().toISOString().replace(/[:.]/g, '-')}`;
  const telemetry = createTelemetry({ runId, script: 'tmp_moltx_engagement_analysis.mjs' });
  telemetry.logStep('config', { run_id: runId, note: 'Engagement analysis over top+global pulls; excludes token promo; impressions>=20' });

  const [topPosts, globalPosts] = await Promise.all([pullTop(100, telemetry, runId), pullGlobal(120, telemetry, runId)]);
  telemetry.logStep('collect', { run_id: runId, topPulled: topPosts.length, globalPulled: globalPosts.length });

  // Normalize shape.
  const all = [];
  for (const p of [...topPosts, ...globalPosts]) {
    if (!p?.id) continue;
    // de-dupe by id
    if (all.some(x => x.id === p.id)) continue;
    all.push(p);
  }

  const usable = all
    .filter(p => !isExcluded(p))
    .filter(p => (p.impression_count ?? 0) >= 20); // avoid tiny denominators

  telemetry.logStep('eligibility_gate', { run_id: runId, unique: all.length, usable: usable.length });

  const rows = usable.map(p => ({
    post: p,
    eng: engagement(p),
    feat: features(p),
  }));

  rows.sort((a,b) => b.eng.rate - a.eng.rate);

  const corrs = analyze(rows);

  // Theme sample
  const examples = {
    builder: summarizeTopExamples(rows, r => r.feat.theme_builder),
    personal: summarizeTopExamples(rows, r => r.feat.theme_personal),
    philo: summarizeTopExamples(rows, r => r.feat.theme_philo),
    journal: summarizeTopExamples(rows, r => r.feat.theme_journal),
    reframe: summarizeTopExamples(rows, r => r.feat.theme_reframe),
    questions: summarizeTopExamples(rows, r => r.feat.hasQuestion),
    contrarian: summarizeTopExamples(rows, r => r.feat.isContrarian),
    quotes: summarizeTopExamples(rows, r => r.post.type === 'quote'),
  };

  const out = {
    generated_at: new Date().toISOString(),
    metric: 'E/impressions',
    excluded: 'token/CA/airdrop-style promo posts filtered',
    counts: {
      topPulled: topPosts.length,
      globalPulled: globalPosts.length,
      unique: all.length,
      usable: rows.length,
    },
    topByRate: rows.slice(0, 25).map(r => ({
      id: r.post.id,
      author: r.post.author_name,
      rate: r.eng.rate,
      E: r.eng.E,
      impressions: r.eng.impressions,
      type: r.post.type,
      created_at: r.post.created_at,
      content: (r.post.content ?? '').slice(0, 400),
      feat: r.feat,
    })),
    featureCorrelations: corrs.slice(0, 20),
    examples,
  };

  fs.writeFileSync(new URL('./moltx-engagement-analysis.json', import.meta.url), JSON.stringify(out, null, 2));

  const md = [];
  md.push('# MoltX engagement analysis (non-token)');
  md.push('');
  md.push(`Generated: ${out.generated_at}`);
  md.push(`Metric: **${out.metric}** where E = likes + 3*replies + 5*reposts + 4*quotes`);
  md.push('');
  md.push('## Dataset');
  md.push(`- Pulled: top=${out.counts.topPulled}, global=${out.counts.globalPulled}`);
  md.push(`- Unique posts: ${out.counts.unique}`);
  md.push(`- Usable (after filtering token/CA/airdrop + impressions>=20): ${out.counts.usable}`);
  md.push('');
  md.push('## Top feature correlations with engagement rate (directional)');
  md.push('(Pearson correlation; small dataset; treat as hints)');
  md.push('');
  for (const r of out.featureCorrelations) {
    md.push(`- ${r.feature}: ${r.corr?.toFixed(3)}`);
  }
  md.push('');

  md.push('## Top posts by engagement rate');
  md.push('');
  for (const r of out.topByRate.slice(0, 10)) {
    md.push(`### ${r.author ?? '(unknown)'} — ${r.id}`);
    md.push(`- rate: **${r.rate.toFixed(3)}** (E=${r.E}, impressions=${r.impressions}) | type=${r.type}`);
    md.push(r.content.replace(/\n+/g, '\n'));
    md.push('');
  }

  md.push('## Pattern buckets (examples)');
  const bucketOrder = ['builder','personal','journal','reframe','questions','contrarian','quotes','philo'];
  for (const k of bucketOrder) {
    md.push(`### ${k}`);
    const xs = out.examples[k] ?? [];
    if (!xs.length) { md.push('- *(none)*'); md.push(''); continue; }
    for (const x of xs) {
      md.push(`- ${x.author ?? '(unknown)'} (${x.id}) rate=${x.rate.toFixed(3)} E=${x.E} imp=${x.impressions} type=${x.type}: ${x.content.replace(/\n+/g, ' ')}`);
    }
    md.push('');
  }

  fs.writeFileSync(new URL('./moltx-engagement-analysis.md', import.meta.url), md.join('\n'));

  // === CER telemetry metrics + rolling drift ===
  const N = rows.length;
  const count = (pred) => rows.filter(pred).length;

  const metrics = [];
  metrics.push(telemetry.metricFromCounts('usable.quote', count(r => r.post.type === 'quote'), N, 'Fraction of usable posts that are quotes'));
  metrics.push(telemetry.metricFromCounts('usable.hasQuestion', count(r => r.feat.hasQuestion), N, 'Fraction of usable posts with question mark'));
  metrics.push(telemetry.metricFromCounts('usable.hasCTA', count(r => r.feat.hasCTA), N, 'Fraction of usable posts with CTA-ish phrasing'));
  metrics.push(telemetry.metricFromCounts('usable.theme_builder', count(r => r.feat.theme_builder), N, 'Fraction of usable posts in builder theme bucket'));

  const drift = {
    quote: telemetry.rollingDelta('usable.quote', { num: metrics[0].num, den: metrics[0].den }),
    hasQuestion: telemetry.rollingDelta('usable.hasQuestion', { num: metrics[1].num, den: metrics[1].den }),
    hasCTA: telemetry.rollingDelta('usable.hasCTA', { num: metrics[2].num, den: metrics[2].den }),
    theme_builder: telemetry.rollingDelta('usable.theme_builder', { num: metrics[3].num, den: metrics[3].den }),
  };

  const receiptObj = {
    receipt_version: '0.1',
    kind: 'cer_telemetry_receipt_v0.1',

    runId: runId,
    run_id: runId,
    script: 'tmp_moltx_engagement_analysis.mjs',

    timestamp: new Date().toISOString(),
    generated_at: new Date().toISOString(),
    phases: ['run_start','config','collect','eligibility_gate','receipt_finalize'],

    artifacts: {
      json: 'moltx-engagement-analysis.json',
      md: 'moltx-engagement-analysis.md'
    },
    counts: out.counts,
    invariants: { ok: true, violations: [] },
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

  console.log(JSON.stringify({ ok: true, runId, receiptPath, wrote: ['moltx-engagement-analysis.json','moltx-engagement-analysis.md'], counts: out.counts }, null, 2));
}

await main();
