import { DurableObject } from 'cloudflare:workers';

const SITE_ORIGIN = 'https://espierin.github.io';
const RESULT_INDEX = 'https://raw.githubusercontent.com/espierin/overtakeitaway/goat-ai-results/index.json';
const GITHUB_API = 'https://api.github.com';
const MAX_BODY = 4096;
const MAX_QUEUE_AGE_MS = 25 * 60 * 1000;

function cors(origin) {
  return {
    'Access-Control-Allow-Origin': origin === SITE_ORIGIN ? SITE_ORIGIN : 'null',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Cache-Control': 'no-store',
    'Content-Type': 'application/json; charset=utf-8',
    'Vary': 'Origin',
    'X-Content-Type-Options': 'nosniff',
  };
}

function response(origin, status, body) {
  return new Response(JSON.stringify(body), { status, headers: cors(origin) });
}

function validRequest(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const { drivers, from, to, circuits, lang, curveyears, prompt_sha256: hash } = value;
  const slug = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  return Array.isArray(drivers) && drivers.length >= 2 && drivers.length <= 4 &&
    drivers.every(id => typeof id === 'string' && slug.test(id)) && new Set(drivers).size === drivers.length &&
    Number.isInteger(from) && Number.isInteger(to) && from >= 1950 && from <= to && to <= 2100 &&
    Array.isArray(circuits) && circuits.length <= 100 && circuits.every(id => typeof id === 'string' && slug.test(id)) &&
    (lang === 'nl' || lang === 'en') && (curveyears === 'career' || curveyears === 'calendar') &&
    typeof hash === 'string' && /^[a-f0-9]{64}$/.test(hash);
}

async function digest(text) {
  const bytes = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(hash)].map(value => value.toString(16).padStart(2, '0')).join('');
}

async function cached(hash) {
  const result = await fetch(`${RESULT_INDEX}?t=${Date.now()}`, {
    headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
    cf: { cacheTtl: 0, cacheEverything: false },
  });
  if (result.status === 404) return false;
  if (!result.ok) throw new Error('result_index_unavailable');
  const index = await result.json();
  return Boolean(index?.results?.[hash]);
}

async function claim(env, hash, ipHash, day, now) {
  const id = env.REQUEST_BUDGET.idFromName('global');
  const stub = env.REQUEST_BUDGET.get(id);
  const result = await stub.fetch('https://budget.internal/claim', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hash, ipHash, day, now,
      globalLimit: Number(env.GLOBAL_DAILY_LIMIT) || 4,
      ipLimit: Number(env.PER_IP_DAILY_LIMIT) || 2,
    }),
  });
  return result.json();
}

async function finish(env, hash, status) {
  const stub = env.REQUEST_BUDGET.get(env.REQUEST_BUDGET.idFromName('global'));
  await stub.fetch('https://budget.internal/finish', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hash, status }),
  });
}

export class RequestBudget extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    ctx.blockConcurrencyWhile(async () => {
      this.sql.exec(`CREATE TABLE IF NOT EXISTS submissions (
        hash TEXT PRIMARY KEY, day TEXT NOT NULL, ip_hash TEXT NOT NULL,
        created_at INTEGER NOT NULL, attempts INTEGER NOT NULL, status TEXT NOT NULL
      )`);
      this.sql.exec(`CREATE TABLE IF NOT EXISTS daily_counts (
        day TEXT PRIMARY KEY, count INTEGER NOT NULL
      )`);
      this.sql.exec(`CREATE TABLE IF NOT EXISTS ip_counts (
        day TEXT NOT NULL, ip_hash TEXT NOT NULL, count INTEGER NOT NULL,
        PRIMARY KEY (day, ip_hash)
      )`);
    });
  }

  async fetch(request) {
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });
    const url = new URL(request.url);
    const value = await request.json();
    if (url.pathname === '/finish') {
      if (!/^[a-f0-9]{64}$/.test(value.hash || '') || !['queued', 'failed'].includes(value.status)) {
        return Response.json({ error: 'invalid_finish' }, { status: 400 });
      }
      this.sql.exec('UPDATE submissions SET status = ?, created_at = ? WHERE hash = ?', value.status, Date.now(), value.hash);
      return Response.json({ ok: true });
    }
    if (url.pathname !== '/claim' || !/^[a-f0-9]{64}$/.test(value.hash || '') ||
        !/^[a-f0-9]{64}$/.test(value.ipHash || '') || !/^\d{4}-\d{2}-\d{2}$/.test(value.day || '')) {
      return Response.json({ error: 'invalid_claim' }, { status: 400 });
    }

    const now = Number(value.now);
    const day = value.day;
    const current = this.sql.exec('SELECT hash, created_at, attempts, status FROM submissions WHERE hash = ?', value.hash).toArray()[0];
    if (current && current.status === 'queued' && now - current.created_at < MAX_QUEUE_AGE_MS) {
      return Response.json({ allowed: false, reason: 'already_queued' });
    }
    if (current && current.attempts >= 2) return Response.json({ allowed: false, reason: 'retry_limit' });
    if (current && current.status === 'failed' && now - current.created_at < 60_000) {
      return Response.json({ allowed: false, reason: 'already_queued' });
    }

    const globalCount = this.sql.exec('SELECT count FROM daily_counts WHERE day = ?', day).toArray()[0]?.count || 0;
    if (globalCount >= Math.max(1, Math.min(10, Number(value.globalLimit) || 4))) {
      return Response.json({ allowed: false, reason: 'daily_limit' });
    }
    const ipCount = this.sql.exec('SELECT count FROM ip_counts WHERE day = ? AND ip_hash = ?', day, value.ipHash).toArray()[0]?.count || 0;
    if (ipCount >= Math.max(1, Math.min(4, Number(value.ipLimit) || 2))) {
      return Response.json({ allowed: false, reason: 'ip_limit' });
    }

    this.sql.exec(`INSERT INTO daily_counts(day, count) VALUES (?, 1)
      ON CONFLICT(day) DO UPDATE SET count = count + 1`, day);
    this.sql.exec(`INSERT INTO ip_counts(day, ip_hash, count) VALUES (?, ?, 1)
      ON CONFLICT(day, ip_hash) DO UPDATE SET count = count + 1`, day, value.ipHash);
    if (current) {
      this.sql.exec('UPDATE submissions SET day = ?, ip_hash = ?, created_at = ?, attempts = attempts + 1, status = ? WHERE hash = ?',
        day, value.ipHash, now, 'queued', value.hash);
    } else {
      this.sql.exec('INSERT INTO submissions(hash, day, ip_hash, created_at, attempts, status) VALUES (?, ?, ?, ?, 1, ?)',
        value.hash, day, value.ipHash, now, 'queued');
    }
    this.sql.exec('DELETE FROM daily_counts WHERE day < ?', day);
    this.sql.exec('DELETE FROM ip_counts WHERE day < ?', day);
    this.sql.exec('DELETE FROM submissions WHERE created_at < ?', now - 8 * 24 * 60 * 60 * 1000);
    return Response.json({ allowed: true, reason: current ? 'retry' : 'new' });
  }
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    if (request.method === 'OPTIONS') {
      if (origin !== SITE_ORIGIN) return response(origin, 403, { error: 'origin_not_allowed' });
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    if (origin !== SITE_ORIGIN) return response(origin, 403, { error: 'origin_not_allowed' });
    if (new URL(request.url).pathname !== '/request') return response(origin, 404, { error: 'not_found' });
    if (request.method !== 'POST') return response(origin, 405, { error: 'method_not_allowed' });
    if (!(request.headers.get('Content-Type') || '').toLowerCase().startsWith('application/json')) {
      return response(origin, 415, { error: 'json_required' });
    }
    const length = Number(request.headers.get('Content-Length') || 0);
    if (length > MAX_BODY) return response(origin, 413, { error: 'request_too_large' });

    let body;
    try {
      const text = await request.text();
      if (new TextEncoder().encode(text).byteLength > MAX_BODY) return response(origin, 413, { error: 'request_too_large' });
      body = JSON.parse(text);
    } catch {
      return response(origin, 400, { error: 'invalid_json' });
    }
    if (!validRequest(body)) return response(origin, 400, { error: 'invalid_request' });
    if (!env.GITHUB_ACTIONS_TOKEN || !env.RATE_LIMIT_SALT) return response(origin, 503, { error: 'request_service_not_configured' });

    const ids = [...body.drivers].sort();
    try {
      if (await cached(body.prompt_sha256)) return response(origin, 200, { status: 'cached' });
    } catch {
      return response(origin, 503, { error: 'saved_results_temporarily_unavailable' });
    }

    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const day = new Date().toISOString().slice(0, 10);
    const ipHash = await digest(`${env.RATE_LIMIT_SALT || 'oia-public-site'}:${day}:${ip}`);
    const gate = await claim(env, body.prompt_sha256, ipHash, day, Date.now());
    if (!gate.allowed) {
      const limited = ['daily_limit', 'ip_limit', 'retry_limit'].includes(gate.reason);
      return response(origin, limited ? 429 : 202, { status: gate.reason });
    }

    const inputs = {
      drivers: ids.join(','), from: String(body.from), to: String(body.to),
      circuits: [...body.circuits].sort().join(','), lang: body.lang,
      curveyears: body.curveyears, prompt_sha256: body.prompt_sha256,
    };
    try {
      const result = await fetch(`${GITHUB_API}/repos/${env.GITHUB_REPOSITORY}/actions/workflows/${env.GITHUB_WORKFLOW}/dispatches`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.GITHUB_ACTIONS_TOKEN}`,
          'Accept': 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ref: 'main', inputs }),
      });
      if (result.status !== 204) {
        await finish(env, body.prompt_sha256, 'failed');
        return response(origin, result.status === 401 || result.status === 403 ? 503 : 502,
          { error: 'workflow_dispatch_failed' });
      }
    } catch {
      await finish(env, body.prompt_sha256, 'failed');
      return response(origin, 502, { error: 'workflow_dispatch_failed' });
    }
    return response(origin, 202, { status: 'queued' });
  },
};
