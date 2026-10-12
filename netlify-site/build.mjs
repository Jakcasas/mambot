import { cpSync, copyFileSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));

export function apiOrigin(value) {
  if (!value) throw new Error('Set MAMBOT_API_ORIGIN to the public HTTPS address of the running Mambot backend.');
  let url;
  try { url = new URL(value); } catch { throw new Error('MAMBOT_API_ORIGIN must be a valid HTTPS origin.'); }
  if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('MAMBOT_API_ORIGIN must be a bare HTTPS origin without credentials, path, query or fragment.');
  }
  return url.origin;
}

export function build({ source = resolve(HERE, '..', 'static'), output = resolve(HERE, 'dist'), origin } = {}) {
  const backend = apiOrigin(origin);
  rmSync(output, { recursive: true, force: true });
  const site = join(output, 'mambot');
  mkdirSync(site, { recursive: true });
  cpSync(source, join(site, 'static'), { recursive: true });
  copyFileSync(join(source, 'index.html'), join(site, 'index.html'));
  writeFileSync(join(output, '_redirects'), [
    `/mambot/api/*  ${backend}/mambot/api/:splat  200!`,
    '/mambot  /mambot/  301',
    '/  /mambot/  302',
    '',
  ].join('\n'));
  writeFileSync(join(output, '_headers'), [
    '/mambot/*',
    '  X-Content-Type-Options: nosniff',
    '  X-Frame-Options: SAMEORIGIN',
    '  Referrer-Policy: strict-origin-when-cross-origin',
    "  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'",
    '',
  ].join('\n'));
  return site;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(`Netlify site ready: ${build({ origin: process.env.MAMBOT_API_ORIGIN })}`);
}

