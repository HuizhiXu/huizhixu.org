const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');
const expected = readFileSync('.hugo-version', 'utf8').trim();
const actual = execFileSync('hugo', ['version'], { encoding: 'utf8' });
if (!actual.startsWith(`hugo v${expected}+extended`)) {
  console.error(`Expected Hugo ${expected} extended; found ${actual.trim()}`);
  process.exit(1);
}
