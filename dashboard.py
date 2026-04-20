#!/usr/bin/env python3
"""
ASI-Evolve Dashboard — minimal web UI for running experiments.
Double-click 'Open Dashboard.command' to launch.
"""

import http.server
import json
import os
import subprocess
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = str(ROOT / ".venv" / "bin" / "python3")
PORT = 8477

# Track running processes
active_process = None
process_log = []
process_lock = threading.Lock()


def run_command(cmd: list, label: str):
    """Run a command in background, capture output."""
    global active_process, process_log
    with process_lock:
        if active_process and active_process.poll() is None:
            process_log.append({"t": time.time(), "line": "ERROR: Another process is still running."})
            return
        process_log = [{"t": time.time(), "line": f"=== {label} ==="}]

    env = os.environ.copy()
    env["TOKENIZERS_PARALLELISM"] = "false"
    env["OMP_NUM_THREADS"] = "1"
    env["PATH"] = str(ROOT / ".venv" / "bin") + ":" + env.get("PATH", "")

    def _run():
        global active_process
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=str(ROOT), env=env, text=True, bufsize=1
            )
            with process_lock:
                active_process = proc
            for line in proc.stdout:
                with process_lock:
                    process_log.append({"t": time.time(), "line": line.rstrip()})
            proc.wait()
            with process_lock:
                process_log.append({"t": time.time(), "line": f"\n=== Done (exit {proc.returncode}) ==="})
                active_process = None
        except Exception as e:
            with process_lock:
                process_log.append({"t": time.time(), "line": f"ERROR: {e}"})
                active_process = None

    threading.Thread(target=_run, daemon=True).start()


def get_experiment_status():
    """Gather status info for the dashboard."""
    recipe_dir = ROOT / "experiments" / "recipe_pipeline"
    approved = sorted((recipe_dir / "approved_edits").glob("*.json"))
    cached = sorted(p.name for p in (recipe_dir / "cached_recipes").iterdir() if p.is_dir() or p.is_symlink())

    circle_steps = sorted((ROOT / "experiments" / "circle_packing_demo").glob("steps/step_*"))
    circle_best = None
    for step_dir in reversed(circle_steps):
        results_file = step_dir / "results.json"
        if results_file.exists():
            r = json.loads(results_file.read_text())
            if r.get("success"):
                circle_best = {"step": step_dir.name, "score": r.get("eval_score", 0)}
                break

    return {
        "approved_edits": [f.stem for f in approved],
        "cached_recipes": cached,
        "circle_steps": len(circle_steps),
        "circle_best": circle_best,
        "running": active_process is not None and active_process.poll() is None,
    }


HTML = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>ASI-Evolve Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', sans-serif;
       background: #1a1a2e; color: #e0e0e0; padding: 24px; }
h1 { color: #fff; margin-bottom: 8px; font-size: 22px; }
.subtitle { color: #888; margin-bottom: 24px; font-size: 13px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card { background: #16213e; border-radius: 10px; padding: 18px; }
.card h2 { font-size: 15px; color: #a8b2d1; margin-bottom: 12px; text-transform: uppercase;
           letter-spacing: 1px; font-weight: 500; }
.btn { display: inline-block; padding: 10px 20px; border: none; border-radius: 6px;
       font-size: 14px; font-weight: 600; cursor: pointer; margin: 4px 4px 4px 0;
       transition: opacity 0.2s; }
.btn:hover { opacity: 0.85; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-blue { background: #4361ee; color: #fff; }
.btn-green { background: #2d6a4f; color: #fff; }
.btn-orange { background: #e76f51; color: #fff; }
.stat { display: inline-block; background: #0f3460; border-radius: 6px;
        padding: 6px 12px; margin: 3px 3px 3px 0; font-size: 13px; }
.stat b { color: #4cc9f0; }
.log { background: #0d1117; border-radius: 8px; padding: 14px; font-family: 'SF Mono', monospace;
       font-size: 12px; height: 320px; overflow-y: auto; white-space: pre-wrap;
       line-height: 1.5; color: #c9d1d9; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
              margin-right: 6px; vertical-align: middle; }
.dot-green { background: #2dd4bf; }
.dot-gray { background: #555; }
.dot-pulse { animation: pulse 1s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
label.file-label { display: inline-block; padding: 10px 20px; border-radius: 6px;
                   background: #2d6a4f; color: #fff; font-size: 14px; font-weight: 600;
                   cursor: pointer; margin: 4px 4px 4px 0; }
label.file-label:hover { opacity: 0.85; }
input[type=file] { display: none; }
.recipe-list { font-size: 13px; color: #a8b2d1; margin-top: 8px; }
.dropzone { border: 2px dashed #4361ee44; border-radius: 10px; padding: 32px 18px;
            text-align: center; color: #556; font-size: 14px; margin-top: 12px;
            transition: all 0.2s; }
.dropzone.over { border-color: #4361ee; background: #4361ee18; color: #a8b2d1; }
.dropzone.success { border-color: #2dd4bf; background: #2dd4bf12; }
</style>
</head><body>
<h1>ASI-Evolve Dashboard</h1>
<p class="subtitle">Recipe pipeline evolution + circle packing experiments</p>

<div class="grid">
  <div class="card">
    <h2>Circle Packing Demo</h2>
    <p style="font-size:13px; color:#888; margin-bottom:12px;">
      Validates the full researcher &rarr; engineer &rarr; analyzer loop with Claude CLI.
    </p>
    <button class="btn btn-blue" onclick="runCirclePacking()" id="btn-circle">
      Run 2-Step Demo
    </button>
    <div id="circle-status" style="margin-top:10px;"></div>
  </div>

  <div class="card">
    <h2>Recipe Ground Truth</h2>
    <div class="dropzone" id="dropzone">
      Drag &amp; drop Premiere FCP XML files here
      <br><span style="font-size:12px; color:#445;">or click to browse</span>
      <input type="file" accept=".xml" multiple id="file-input" style="display:none">
    </div>
    <div style="margin-top:10px;">
      <button class="btn btn-orange" onclick="scoreBaseline()" id="btn-score">
        Score Baseline
      </button>
    </div>
    <div id="recipe-status" style="margin-top:10px;"></div>
  </div>
</div>

<div class="card" style="margin-bottom:16px;">
  <h2><span class="status-dot dot-gray" id="run-dot"></span> Output Log</h2>
  <div class="log" id="log"></div>
</div>

<script>
const API = '';
let pollTimer = null;

async function api(path, opts) {
  const r = await fetch(API + path, opts);
  return r.json();
}

async function runCirclePacking() {
  document.getElementById('btn-circle').disabled = true;
  await api('/api/run-circle-packing');
  startPolling();
}

async function scoreBaseline() {
  document.getElementById('btn-score').disabled = true;
  await api('/api/score-baseline');
  startPolling();
}

async function uploadXML(files) {
  for (const file of files) {
    const form = new FormData();
    form.append('file', file);
    const r = await fetch(API + '/api/upload-xml', { method: 'POST', body: form });
    const j = await r.json();
    appendLog('Upload: ' + j.message);
  }
  refreshStatus();
}

function appendLog(line) {
  const log = document.getElementById('log');
  log.textContent += line + '\\n';
  log.scrollTop = log.scrollHeight;
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(pollLog, 500);
}

let lastLogLen = 0;
async function pollLog() {
  const data = await api('/api/log?since=' + lastLogLen);
  const log = document.getElementById('log');
  const dot = document.getElementById('run-dot');

  if (data.lines && data.lines.length > 0) {
    for (const l of data.lines) {
      log.textContent += l.line + '\\n';
    }
    log.scrollTop = log.scrollHeight;
    lastLogLen += data.lines.length;
  }

  if (data.running) {
    dot.className = 'status-dot dot-green dot-pulse';
  } else {
    dot.className = 'status-dot dot-gray';
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    document.getElementById('btn-circle').disabled = false;
    document.getElementById('btn-score').disabled = false;
    refreshStatus();
  }
}

async function refreshStatus() {
  const s = await api('/api/status');
  let html = '';
  if (s.circle_best) {
    html += '<span class="stat">Best: <b>' + s.circle_best.score.toFixed(3) + '</b> (' + s.circle_best.step + ')</span> ';
  }
  html += '<span class="stat">Steps: <b>' + s.circle_steps + '</b></span>';
  document.getElementById('circle-status').innerHTML = html;

  let rhtml = '<div class="recipe-list">';
  rhtml += '<b>Cached:</b> ' + s.cached_recipes.join(', ') + '<br>';
  rhtml += '<b>Approved:</b> ' + (s.approved_edits.length ? s.approved_edits.join(', ') : '<em>none yet</em>');
  rhtml += '</div>';
  document.getElementById('recipe-status').innerHTML = rhtml;
}

// Drag and drop
const dz = document.getElementById('dropzone');
const fi = document.getElementById('file-input');

dz.addEventListener('click', () => fi.click());
fi.addEventListener('change', () => { if (fi.files.length) uploadXML(fi.files); });

dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', (e) => {
  e.preventDefault();
  dz.classList.remove('over');
  const files = [...e.dataTransfer.files].filter(f => f.name.endsWith('.xml'));
  if (files.length === 0) {
    appendLog('No .xml files found in drop');
    return;
  }
  uploadXML(files);
  dz.classList.add('success');
  setTimeout(() => dz.classList.remove('success'), 2000);
});

// Prevent page-level drop from navigating away
document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => e.preventDefault());

refreshStatus();
</script>
</body></html>"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _html(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode())

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._html(HTML)

        elif path == "/api/status":
            self._json(get_experiment_status())

        elif path == "/api/log":
            params = urllib.parse.parse_qs(parsed.query)
            since = int(params.get("since", [0])[0])
            with process_lock:
                lines = process_log[since:]
                running = active_process is not None and active_process.poll() is None
            self._json({"lines": lines, "running": running})

        elif path == "/api/run-circle-packing":
            run_command(
                [VENV_PYTHON, "main.py", "--experiment", "circle_packing_demo",
                 "--steps", "2", "--sample-n", "3",
                 "--eval-script", str(ROOT / "experiments" / "circle_packing_demo" / "eval.sh")],
                "Circle Packing Demo (2 steps)"
            )
            self._json({"ok": True})

        elif path == "/api/score-baseline":
            run_command(
                [VENV_PYTHON, str(ROOT / "experiments" / "recipe_pipeline" / "evaluator.py"),
                 str(ROOT / "experiments" / "recipe_pipeline" / "initial_program"),
                 str(ROOT / "experiments" / "recipe_pipeline" / "baseline_results.json")],
                "Scoring baseline config against approved edits"
            )
            self._json({"ok": True})

        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/upload-xml":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Parse multipart form data (simple extraction)
            boundary = self.headers.get("Content-Type", "").split("boundary=")[-1]
            if not boundary:
                self._json({"error": "No boundary"}, 400)
                return

            # Find the file content between boundaries
            parts = body.split(b"--" + boundary.encode())
            for part in parts:
                if b"filename=" not in part:
                    continue

                # Extract filename
                header_end = part.find(b"\r\n\r\n")
                if header_end < 0:
                    continue
                headers = part[:header_end].decode(errors="replace")
                file_data = part[header_end + 4:]
                if file_data.endswith(b"\r\n"):
                    file_data = file_data[:-2]

                filename = ""
                for h in headers.split("\r\n"):
                    if "filename=" in h:
                        filename = h.split('filename="')[1].split('"')[0]
                        break

                if not filename:
                    continue

                # Save XML
                xml_path = ROOT / "experiments" / "recipe_pipeline" / "approved_edits" / filename
                xml_path.write_bytes(file_data)

                # Convert to JSON manifest
                recipe_name = Path(filename).stem
                json_path = xml_path.parent / f"{recipe_name}.json"

                try:
                    import importlib.util as ilu
                    spec = ilu.spec_from_file_location(
                        "xml_parser",
                        ROOT / "experiments" / "recipe_pipeline" / "xml_to_manifest.py"
                    )
                    mod = ilu.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    manifest = mod.parse_premiere_xml(str(xml_path))
                    json_path.write_text(json.dumps(manifest, indent=2))
                    n_clips = len(manifest.get("timeline", []))
                    self._json({"message": f"{filename} -> {recipe_name}.json ({n_clips} clips)"})
                except Exception as e:
                    # Keep the XML, report error
                    self._json({"message": f"Saved {filename} but XML parse failed: {e}"})
                return

            self._json({"error": "No file found in upload"}, 400)
        else:
            self.send_error(404)


def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), DashboardHandler)
    print(f"ASI-Evolve Dashboard running at http://127.0.0.1:{PORT}")
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
