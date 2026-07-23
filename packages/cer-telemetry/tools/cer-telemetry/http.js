function nowIso() { return new Date().toISOString(); }

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

export class ThrottleError extends Error {
  constructor(message, { status, url } = {}) {
    super(message);
    this.name = 'ThrottleError';
    this.status = status;
    this.url = url;
  }
}

export class Blocked403Error extends Error {
  constructor(message, { status = 403, url } = {}) {
    super(message);
    this.name = 'Blocked403Error';
    this.status = status;
    this.url = url;
  }
}

function jitterMs(maxJitterMs) {
  const j = Number(maxJitterMs ?? 0);
  if (!Number.isFinite(j) || j <= 0) return 0;
  return Math.floor(Math.random() * j);
}

function isBlocked403(resStatus, msg) {
  if (resStatus !== 403) return false;
  return String(msg ?? '').toLowerCase().includes('blocked');
}

/**
 * resilientJsonGet(url, { headers, telemetry, phaseCtx, retry, tolerate403 })
 *
 * - Retries 429/5xx with exp backoff + jitter
 * - Retries 403 Blocked with blocked403DelayMs, then either throws Blocked403Error
 *   or (if tolerate403=true) still throws Blocked403Error for caller to tolerate/stop paging.
 * - Returns parsed JSON body on success.
 */
export async function resilientJsonGet(url, {
  headers,
  telemetry,
  phaseCtx,
  retry,
  tolerate403 = false,
  retries = 6,
} = {}) {
  const cfg = {
    baseDelayMs: Number(retry?.baseDelayMs ?? 600),
    blocked403DelayMs: Number(retry?.blocked403DelayMs ?? 60_000),
    jitterMs: Number(retry?.jitterMs ?? 200),
  };

  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, { headers });
      const text = await res.text();

      let json;
      try { json = JSON.parse(text); } catch {
        throw new Error(`Non-JSON ${res.status} from ${url}: ${text.slice(0, 200)}`);
      }

      if (!res.ok || json?.success === false) {
        const msg = typeof json?.error === 'string' ? json.error : text.slice(0, 500);

        const retryable = [429, 500, 502, 503, 504].includes(res.status) || isBlocked403(res.status, msg);
        if (!retryable) {
          throw new Error(`HTTP ${res.status} from ${url}: ${msg}`);
        }

        // classified retryable
        if (isBlocked403(res.status, msg)) {
          lastErr = new Blocked403Error(`HTTP 403 Blocked from ${url}: ${msg}`, { status: 403, url });
        } else {
          lastErr = new ThrottleError(`Retryable HTTP ${res.status} from ${url}: ${msg}`, { status: res.status, url });
        }
        throw lastErr;
      }

      return json;
    } catch (e) {
      lastErr = e;
      if (attempt >= retries) break;

      const msg = String(e?.message ?? e);
      const blocked = e?.name === 'Blocked403Error' || (msg.includes('HTTP 403') && msg.toLowerCase().includes('blocked'));

      // If caller will tolerate 403 by breaking a paging loop, surface it immediately.
      // This prevents long hangs/timeouts during MoltX throttling.
      if (blocked && tolerate403) {
        telemetry?.logStep?.('network_throttle', {
          ts: nowIso(),
          url,
          status: e?.status ?? 403,
          attempt,
          blocked403: true,
          delay_ms: 0,
          phase: phaseCtx ?? null,
          note: 'tolerate403=true; throwing immediately to allow partial results'
        });
        throw e;
      }

      const delay = blocked
        ? (cfg.blocked403DelayMs + jitterMs(cfg.jitterMs))
        : (cfg.baseDelayMs * Math.pow(1.6, attempt) + jitterMs(cfg.jitterMs));

      if (telemetry?.logStep) {
        telemetry.logStep('network_throttle', {
          ts: nowIso(),
          url,
          status: e?.status ?? null,
          attempt,
          blocked403: blocked,
          delay_ms: Math.round(delay),
          phase: phaseCtx ?? null,
        });
      }

      await sleep(delay);
      continue;
    }
  }

  // If caller wants to tolerate 403, we still throw a typed error so caller can break loops.
  if (lastErr?.name === 'Blocked403Error' && tolerate403) throw lastErr;
  throw lastErr;
}
