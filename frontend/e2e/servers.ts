import { spawn, type ChildProcess } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const frontend = fileURLToPath(new URL('..', import.meta.url));
const root = path.resolve(frontend, '..');
const database = path.resolve(root, '.venv', `phase8-e2e-${process.pid}-${Date.now()}.sqlite3`);
let backend: ChildProcess | null = null, ui: ChildProcess | null = null;
let logs = '';
function launch(command: string, args: string[], cwd: string, extra: Record<string, string> = {}): ChildProcess {
  const process = spawn(command, args, { cwd, env: { ...globalThis.process.env, ...extra }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  process.stdout?.on('data', value => { logs = (logs + value).slice(-8000); });
  process.stderr?.on('data', value => { logs = (logs + value).slice(-8000); });
  return process;
}
async function ready(url: string, child: ChildProcess) {
  const end = Date.now() + 30_000;
  while (Date.now() < end) {
    if (child.exitCode !== null) throw new Error(`Owned test server exited. ${logs}`);
    try { const response = await fetch(url, { signal: AbortSignal.timeout(1000) }); if (response.ok) return; } catch { /* Retry startup only. */ }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Owned test server did not become ready. ${logs}`);
}
export async function startServers() {
  const python = process.env.QUANTLAB_PYTHON || path.resolve(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  backend = launch(python, ['-m', 'quantlab.api', '--database', database, '--port', '8018'], root, { PYTHONUNBUFFERED: '1' });
  await ready('http://127.0.0.1:8018/api/v1/health', backend);
  ui = launch(process.execPath, [path.resolve(frontend, 'node_modules/vite/bin/vite.js'), 'preview', '--host', '127.0.0.1', '--port', '5178', '--strictPort'], frontend,
    { QUANTLAB_API_TARGET: 'http://127.0.0.1:8018' });
  await ready('http://127.0.0.1:5178', ui);
}
async function stop(child: ChildProcess | null) {
  if (!child || child.exitCode !== null) return;
  const closed = new Promise<void>(resolve => child.once('exit', () => resolve()));
  child.kill();
  await Promise.race([closed, new Promise<never>((_, reject) => setTimeout(() => reject(new Error('Owned test server did not stop.')), 5000))]);
}
export async function stopServers() { await stop(ui); ui = null; await stop(backend); backend = null; }
export { frontend };
