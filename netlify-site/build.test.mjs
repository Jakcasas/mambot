import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { apiOrigin, build } from './build.mjs';

test('API destination must be a bare HTTPS origin', () => {
  for (const value of ['', 'http://api.example.com', 'https://user:pass@api.example.com',
    'https://api.example.com/path', 'https://api.example.com/?key=x', 'https://api.example.com/#x']) {
    assert.throws(() => apiOrigin(value));
  }
  assert.equal(apiOrigin('https://api.example.com'), 'https://api.example.com');
});

test('build preserves Mambot paths and proxies only API requests', () => {
  const root = mkdtempSync(join(tmpdir(), 'mambot-netlify-'));
  try {
    const source = join(root, 'static');
    const output = join(root, 'dist');
    mkdirSync(join(source, 'js'), { recursive: true });
    writeFileSync(join(source, 'index.html'), '<script src="./static/js/app.js"></script>');
    writeFileSync(join(source, 'js', 'app.js'), 'export default true;');
    build({ source, output, origin: 'https://api.example.com' });
    assert.ok(existsSync(join(output, 'mambot', 'static', 'js', 'app.js')));
    assert.equal(readFileSync(join(output, 'mambot', 'index.html'), 'utf8'),
      '<script src="./static/js/app.js"></script>');
    const redirects = readFileSync(join(output, '_redirects'), 'utf8');
    assert.match(redirects, /^\/mambot\/api\/\*  https:\/\/api\.example\.com\/mambot\/api\/:splat  200!/m);
    assert.match(redirects, /^\/  \/mambot\/  302$/m);
    assert.doesNotMatch(redirects, /\bstatic\/\*\b/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

