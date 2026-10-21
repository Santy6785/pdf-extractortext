import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

function getJsFiles(dir) {
  let results = [];
  const list = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of list) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results = results.concat(getJsFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.js')) {
      results.push(fullPath);
    }
  }
  return results;
}

const targets = ['frontend', 'tests/frontend', 'tests/load'];
let totalChecked = 0;
let errors = 0;

for (const target of targets) {
  if (fs.existsSync(target)) {
    const files = getJsFiles(target);
    for (const file of files) {
      try {
        execFileSync(process.execPath, ['--check', file], { stdio: 'pipe' });
        totalChecked++;
      } catch (err) {
        console.error(`✖ Error de sintaxis en: ${file}\n`, err.stderr?.toString() || err.message);
        errors++;
      }
    }
  }
}

if (errors > 0) {
  console.error(`Lint falló con ${errors} errores en ${totalChecked} archivos.`);
  process.exit(1);
} else {
  console.log(`✔ Lint exitoso: ${totalChecked} archivos JavaScript verificados correctamente sin errores de sintaxis.`);
}
