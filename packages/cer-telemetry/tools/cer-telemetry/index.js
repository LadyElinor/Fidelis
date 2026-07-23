import fs from 'node:fs';
import path from 'node:path';

import { createEventLogger } from './event_logger.js';
import { checkInvariants } from './invariants.js';
import { wilsonInterval, rateDelta } from './stats.js';
import { writeReceipt } from './receipt.js';
export { resilientJsonGet, Blocked403Error, ThrottleError } from './http.js';

function nowIso() { return new Date().toISOString(); }

function loadBaseConfig() {
  const p = new URL('./config.json', import.meta.url);
  const raw = fs.readFileSync(p, 'utf8');
  return JSON.parse(raw);
}

export function createTelemetry({ runId, script, config: scriptConfig, meta } = {}) {
  const config = { ...loadBaseConfig() };
  // allow script to pass invariantsPolicy etc. under meta/config; keep base config for paths
  const logger = createEventLogger({ runId, script, config, meta: { ...meta, scriptConfig } });

  function logStep(phase, data) {
    logger.logStep(phase, data);
  }

  function runInvariants(args) {
    const res = checkInvariants({ ...args, config: { ...scriptConfig, ...config } });
    for (const v of res.violations) logger.logViolation(v);
    return res;
  }

  function metricFromCounts(metric, num, den, notes) {
    const z = config?.wilson?.z ?? 1.96;
    const wi = wilsonInterval(num, den, z);
    logger.logMetric({ metric, num, den, value: wi.value, ci_low: wi.low, ci_high: wi.high, notes });
    return { metric, num, den, ...wi };
  }

  function rollingDelta(metric, currCounts) {
    const lookback = config?.rolling?.lookbackRuns ?? 20;
    const prevAgg = logger.queryRollingMetric(metric, lookback);
    const z = config?.wilson?.z ?? 1.96;
    const prevWi = wilsonInterval(prevAgg.num, prevAgg.den, z);
    const currWi = wilsonInterval(currCounts.num, currCounts.den, z);
    return {
      metric,
      lookback_runs: prevAgg.rows,
      prev: { num: prevAgg.num, den: prevAgg.den, ...prevWi },
      curr: { num: currCounts.num, den: currCounts.den, ...currWi },
      delta: rateDelta(currWi, prevWi),
    };
  }

  function finish({ receiptObj }) {
    const receiptPath = writeReceipt({ runId, receiptDir: config.receipt_dir, receiptObj });
    logger.endRun({ meta: { receiptPath } });
    return receiptPath;
  }

  logStep('run_start', { run_id: runId, script, ts: nowIso() });

  return {
    config,
    logger,
    logStep,
    runInvariants,
    metricFromCounts,
    rollingDelta,
    finish,
  };
}
