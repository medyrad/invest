// Redirect only output paths. Independent requests, assertions and selectors are untouched.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const source = path.join(root, 'docs/stage3/independent-evidence');
const destination = process.env.INVEST_INDEPENDENT_OUTPUT;
const allowed = ['docs/stage3/fix-evidence', '.tools/s03-fix'].map(p => path.join(root, p));
if (!destination || !path.isAbsolute(destination) || !allowed.some(p => destination === p || destination.startsWith(p + path.sep))) {
  throw new Error('An isolated S03 fix evidence directory is required');
}
fs.mkdirSync(destination, { recursive: true });
function redirect(file) {
  if (typeof file !== 'string') return file;
  return file === source || file.startsWith(source + path.sep) ? destination + file.slice(source.length) : file;
}
for (const name of ['writeFileSync', 'createWriteStream', 'mkdirSync']) {
  const original = fs[name];
  fs[name] = function (file, ...args) { return original.call(this, redirect(file), ...args); };
}
for (const name of ['writeFile', 'mkdir']) {
  const original = fs.promises[name];
  fs.promises[name] = function (file, ...args) { return original.call(this, redirect(file), ...args); };
}
