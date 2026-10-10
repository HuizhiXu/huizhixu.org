const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');
function matchesVersion(actual, expected) {
  const version = /^hugo v(\d+\.\d+\.\d+)(?:-[0-9a-f]+)?(\+[^\s]+)?\s/.exec(actual);
  return Boolean(version && version[1] === expected && version[2]?.split('+').includes('extended'));
}
if (require.main === module) {
  const expected = readFileSync('.hugo-version', 'utf8').trim();
  const actual = execFileSync('hugo', ['version'], { encoding: 'utf8' });
  if (!matchesVersion(actual, expected)) {
    console.error(`Expected Hugo ${expected} extended; found ${actual.trim()}`);
    process.exit(1);
  }
}
module.exports = { matchesVersion };
