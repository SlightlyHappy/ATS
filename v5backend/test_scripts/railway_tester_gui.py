import threading
import queue
import json
import time
import mimetypes
import os
import sys
import webbrowser
from tkinter import Tk, StringVar, IntVar, Text, END, BOTH, filedialog, Toplevel, Scrollbar, RIGHT, Y, LEFT, X
from tkinter import messagebox
from tkinter import ttk

try:
    import requests
except ImportError:
    print("This script requires the 'requests' package. Install with: pip install requests")
    raise


class RailwayTesterGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Railway Deployment Tester - ATS Backend")
        self.root.geometry("1100x750")

        self.base_url = StringVar(value=os.environ.get("ATS_API_BASE_URL", "https://<your-railway-url>/api"))
        self.timeout = IntVar(value=30)
        self.chat_running = False
        self.chat_thread = None
        self.ui_queue = queue.Queue()

        # Top controls
        top = ttk.Frame(root)
        top.pack(fill=X, padx=8, pady=6)
        ttk.Label(top, text="Base API URL (ends with /api)").pack(side=LEFT)
        self.base_entry = ttk.Entry(top, textvariable=self.base_url, width=60)
        self.base_entry.pack(side=LEFT, padx=6)
        ttk.Label(top, text="Timeout (s)").pack(side=LEFT, padx=(12, 2))
        ttk.Entry(top, textvariable=self.timeout, width=6).pack(side=LEFT)
        ttk.Button(top, text="Open in Browser", command=self.open_base_in_browser).pack(side=LEFT, padx=8)
        # New: Load .env.api
        ttk.Button(top, text="Load .env.api", command=self.load_env_api).pack(side=LEFT)

        # Notebook tabs
        self.nb = ttk.Notebook(root)
        self.nb.pack(fill=BOTH, expand=True)

        self._build_connection_tab()
        self._build_storage_db_tab()
        self._build_upload_tab()
        self._build_search_tab()
        self._build_chat_tab()
        self._build_status_tab()

        # Log panel at bottom
        self._build_log_panel()

        # UI queue processor
        self.root.after(100, self._process_ui_queue)

        # Try auto-load ../.env.api if present
        self.try_autoload_env()

    # ---------- UI Builders ----------
    def _build_connection_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Connection & Health")

        row = ttk.Frame(f)
        row.pack(fill=X, pady=6, padx=8)
        ttk.Button(row, text="Check /api/health", command=self.run_health).pack(side=LEFT)
        ttk.Button(row, text="Check /", command=self.run_root_health).pack(side=LEFT, padx=6)
        ttk.Button(row, text="Health Details", command=self.run_health_details).pack(side=LEFT, padx=6)
        ttk.Button(row, text="Metrics (browser)", command=self.open_metrics).pack(side=LEFT, padx=6)

        self.conn_output = self._make_scrolled_text(f, height=18)

    def _build_storage_db_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Storage & DB")

        row = ttk.Frame(f)
        row.pack(fill=X, pady=6, padx=8)
        ttk.Button(row, text="Debug Config", command=self.run_debug_config).pack(side=LEFT)
        ttk.Button(row, text="S3 Test", command=self.run_s3_test).pack(side=LEFT, padx=6)
        ttk.Button(row, text="Run Alembic Migrate", command=self.run_migrate).pack(side=LEFT, padx=6)
        ttk.Button(row, text="SQL Fallback Migrate", command=self.run_migrate_sql).pack(side=LEFT, padx=6)

        self.store_output = self._make_scrolled_text(f, height=18)

    def _build_upload_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Upload & Resume")

        row1 = ttk.Frame(f)
        row1.pack(fill=X, pady=6, padx=8)
        ttk.Button(row1, text="Select & Upload Files", command=self.run_upload_files).pack(side=LEFT)

        row2 = ttk.Frame(f)
        row2.pack(fill=X, pady=6, padx=8)
        ttk.Label(row2, text="Resume ID").pack(side=LEFT)
        self.resume_id_var = StringVar()
        ttk.Entry(row2, textvariable=self.resume_id_var, width=45).pack(side=LEFT, padx=6)
        ttk.Button(row2, text="Get Resume", command=self.run_get_resume).pack(side=LEFT)

        self.upload_output = self._make_scrolled_text(f, height=18)

    def _build_search_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Search & Match")

        row1 = ttk.Frame(f)
        row1.pack(fill=X, pady=6, padx=8)
        ttk.Label(row1, text="Query").pack(side=LEFT)
        self.search_query = StringVar()
        ttk.Entry(row1, textvariable=self.search_query, width=50).pack(side=LEFT, padx=6)
        ttk.Button(row1, text="Search", command=self.run_search).pack(side=LEFT)

        row2 = ttk.Frame(f)
        row2.pack(fill=X, pady=6, padx=8)
        ttk.Label(row2, text="Job Description").pack(side=LEFT)
        self.match_jd = Text(row2, height=6, width=70)
        self.match_jd.pack(side=LEFT)
        ttk.Button(row2, text="Match", command=self.run_match).pack(side=LEFT, padx=6)

        self.search_output = self._make_scrolled_text(f, height=18)

    def _build_chat_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Chat (SSE)")

        row1 = ttk.Frame(f)
        row1.pack(fill=X, pady=6, padx=8)
        ttk.Label(row1, text="Session ID").pack(side=LEFT)
        self.chat_session = StringVar(value=f"tester-{int(time.time())}")
        ttk.Entry(row1, textvariable=self.chat_session, width=28).pack(side=LEFT, padx=6)
        ttk.Label(row1, text="Message").pack(side=LEFT)
        self.chat_message = StringVar(value="Summarize the top candidates for a Python role.")
        ttk.Entry(row1, textvariable=self.chat_message, width=50).pack(side=LEFT, padx=6)

        row2 = ttk.Frame(f)
        row2.pack(fill=X, pady=6, padx=8)
        ttk.Label(row2, text="Filters (JSON)").pack(side=LEFT)
        self.chat_filters = Text(row2, height=4, width=80)
        self.chat_filters.insert(END, json.dumps({"sections": ["experience", "skills"]}))
        self.chat_filters.pack(side=LEFT)

        row3 = ttk.Frame(f)
        row3.pack(fill=X, pady=6, padx=8)
        ttk.Button(row3, text="Start Chat Stream", command=self.start_chat).pack(side=LEFT)
        ttk.Button(row3, text="Stop", command=self.stop_chat).pack(side=LEFT, padx=6)

        self.chat_output = self._make_scrolled_text(f, height=22)

    def _build_status_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Status & Actions")

        row1 = ttk.Frame(f)
        row1.pack(fill=X, pady=6, padx=8)
        ttk.Button(row1, text="Overview", command=self.run_status_overview).pack(side=LEFT)
        ttk.Button(row1, text="Find Stuck (10m)", command=self.run_status_stuck).pack(side=LEFT, padx=6)
        ttk.Button(row1, text="Ready for Analysis", command=self.run_status_ready).pack(side=LEFT, padx=6)
        ttk.Button(row1, text="Trigger All Ready", command=self.run_trigger_all_ready).pack(side=LEFT, padx=6)

        row2 = ttk.Frame(f)
        row2.pack(fill=X, pady=6, padx=8)
        ttk.Label(row2, text="Resume ID").pack(side=LEFT)
        self.action_resume_id = StringVar()
        ttk.Entry(row2, textvariable=self.action_resume_id, width=42).pack(side=LEFT, padx=6)
        ttk.Button(row2, text="Trigger Analysis", command=self.run_trigger_one).pack(side=LEFT)

        self.status_output = self._make_scrolled_text(f, height=18)

    def _build_log_panel(self):
        f = ttk.Frame(self.root)
        f.pack(fill=BOTH, expand=False, padx=8, pady=(0, 8))
        ttk.Label(f, text="Log").pack(anchor='w')
        self.log_output = self._make_scrolled_text(f, height=10)

    def _make_scrolled_text(self, parent, height=12):
        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        txt = Text(frame, height=height, wrap='word')
        scr = Scrollbar(frame, command=txt.yview)
        txt.configure(yscrollcommand=scr.set)
        scr.pack(side=RIGHT, fill=Y)
        txt.pack(side=LEFT, fill=BOTH, expand=True)
        return txt

    # ---------- Helpers ----------
    def open_base_in_browser(self):
        url = self.base_url.get().rstrip('/')
        if url.endswith('/api'):
            webbrowser.open(url[:-4])
        else:
            webbrowser.open(url)

    def open_metrics(self):
        base = self.base_url.get().rstrip('/')
        # Base URL is expected to end with /api; open /api/metrics directly
        webbrowser.open(f"{base}/metrics")

    def _append_json(self, widget: Text, data):
        try:
            widget.insert(END, json.dumps(data, indent=2) + "\n\n")
        except Exception:
            widget.insert(END, str(data) + "\n\n")
        widget.see(END)

    def log(self, msg: str):
        ts = time.strftime('%H:%M:%S')
        self.log_output.insert(END, f"[{ts}] {msg}\n")
        self.log_output.see(END)

    # New: .env.api support
    def try_autoload_env(self):
        """Auto-load ../.env.api if it exists and derive base URL."""
        default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env.api"))
        if os.path.exists(default_path):
            try:
                env_map = self._load_env_file(default_path)
                # Derive base URL from RAILWAY_PUBLIC_DOMAIN if present
                derived = self._derive_base_url_from_env(env_map)
                if derived:
                    self.base_url.set(derived)
                self.ui_queue.put(("log", f"Loaded .env.api from {default_path} ({len(env_map)} vars). Base URL: {self.base_url.get()}"))
            except Exception as e:
                self.ui_queue.put(("log", f"Failed to auto-load .env.api: {e}"))

    def load_env_api(self):
        """Prompt for .env.api file (default ../.env.api) and load variables into environment."""
        default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env.api"))
        path = default_path if os.path.exists(default_path) else filedialog.askopenfilename(title="Select .env.api", filetypes=[("Env files", ".env .env.api .txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            env_map = self._load_env_file(path)
            derived = self._derive_base_url_from_env(env_map)
            if derived:
                self.base_url.set(derived)
            self.ui_queue.put(("log", f"Loaded {len(env_map)} variables from {path}. Base URL: {self.base_url.get()}"))
        except Exception as e:
            self.ui_queue.put(("error", f"Failed to load env file: {e}"))

    def _load_env_file(self, path: str) -> dict:
        """Parse a simple .env file and export to os.environ. Returns the parsed key->value map."""
        env_map: dict[str, str] = {}
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if line.lower().startswith('export '):
                    line = line[7:].strip()
                if '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
                # Trim surrounding quotes
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                # Normalize booleans to lowercase strings
                if val.lower() in {"true", "false"}:
                    val = val.lower()
                env_map[key] = val
                os.environ[key] = val
        # Provide ATS_API_BASE_URL if derivable and not set
        if 'ATS_API_BASE_URL' not in os.environ:
            derived = self._derive_base_url_from_env(env_map)
            if derived:
                os.environ['ATS_API_BASE_URL'] = derived
        return env_map

    def _derive_base_url_from_env(self, env_map: dict | None = None) -> str | None:
        env = env_map or os.environ
        # Prefer explicit ATS_API_BASE_URL, else derive from RAILWAY_PUBLIC_DOMAIN
        base = env.get('ATS_API_BASE_URL')
        if base:
            base = base.rstrip('/')
            if not base.endswith('/api'):
                base = base + '/api'
            return base
        domain = env.get('RAILWAY_PUBLIC_DOMAIN')
        if domain:
            scheme = 'https'
            # If domain appears to be internal or has a scheme already, handle accordingly
            if domain.startswith('http://') or domain.startswith('https://'):
                base_url = domain.rstrip('/')
            else:
                base_url = f"{scheme}://{domain}"
            return base_url.rstrip('/') + '/api'
        return None

    def _api(self, method: str, path: str, *, json_body=None, params=None, files=None, stream=False):
        base = self.base_url.get().rstrip('/')
        url = f"{base}{path}" if path.startswith('/') else f"{base}/{path}"
        t = self.timeout.get() or 30
        headers = {"User-Agent": "railway-tester/1.0"}
        if stream:
            return requests.request(method, url, json=json_body, params=params, files=files, headers=headers, timeout=t, stream=True)
        else:
            r = requests.request(method, url, json=json_body, params=params, files=files, headers=headers, timeout=t)
            r.raise_for_status()
            return r

    def _run_bg(self, fn, on_done=None):
        def _wrap():
            try:
                fn()
            except Exception as e:
                self.ui_queue.put(("error", str(e)))
            finally:
                if on_done:
                    self.ui_queue.put(("done", on_done))
        th = threading.Thread(target=_wrap, daemon=True)
        th.start()

    def _process_ui_queue(self):
        try:
            while True:
                typ, payload = self.ui_queue.get_nowait()
                if typ == "append_conn":
                    self._append_json(self.conn_output, payload)
                elif typ == "append_store":
                    self._append_json(self.store_output, payload)
                elif typ == "append_upload":
                    self._append_json(self.upload_output, payload)
                elif typ == "append_search":
                    self._append_json(self.search_output, payload)
                elif typ == "append_status":
                    self._append_json(self.status_output, payload)
                elif typ == "append_chat":
                    self.chat_output.insert(END, payload)
                    self.chat_output.see(END)
                elif typ == "log":
                    self.log(payload)
                elif typ == "error":
                    messagebox.showerror("Error", payload)
                    self.log(f"Error: {payload}")
                elif typ == "done":
                    if callable(payload):
                        try:
                            payload()
                        except Exception:
                            pass
        except queue.Empty:
            pass
        self.root.after(150, self._process_ui_queue)

    # ---------- Operations ----------
    def run_health(self):
        def work():
            self.ui_queue.put(("log", "Checking /api/health"))
            r = self._api("GET", "/health")
            self.ui_queue.put(("append_conn", r.json()))
        self._run_bg(work)

    def run_root_health(self):
        def work():
            self.ui_queue.put(("log", "Checking /"))
            base = self.base_url.get().rstrip('/')
            if base.endswith('/api'):
                base = base[:-4]
            t = self.timeout.get() or 30
            r = requests.get(base + "/", timeout=t)
            r.raise_for_status()
            self.ui_queue.put(("append_conn", r.json()))
        self._run_bg(work)

    def run_health_details(self):
        def work():
            self.ui_queue.put(("log", "Fetching /api/healthz/details"))
            r = self._api("GET", "/healthz/details")
            self.ui_queue.put(("append_conn", r.json()))
        self._run_bg(work)

    def run_debug_config(self):
        def work():
            self.ui_queue.put(("log", "Fetching /api/debug/config"))
            r = self._api("GET", "/debug/config")
            self.ui_queue.put(("append_store", r.json()))
        self._run_bg(work)

    def run_s3_test(self):
        def work():
            self.ui_queue.put(("log", "POST /api/debug/s3test"))
            r = self._api("POST", "/debug/s3test")
            self.ui_queue.put(("append_store", r.json()))
        self._run_bg(work)

    def run_migrate(self):
        def work():
            self.ui_queue.put(("log", "POST /api/debug/migrate"))
            r = self._api("POST", "/debug/migrate")
            self.ui_queue.put(("append_store", r.json()))
        self._run_bg(work)

    def run_migrate_sql(self):
        def work():
            self.ui_queue.put(("log", "POST /api/debug/migrate-sql"))
            r = self._api("POST", "/debug/migrate-sql")
            self.ui_queue.put(("append_store", r.json()))
        self._run_bg(work)

    def run_upload_files(self):
        paths = filedialog.askopenfilenames(title="Select resume files")
        if not paths:
            return

        def work():
            files = []
            opened = []
            try:
                for p in paths:
                    mime, _ = mimetypes.guess_type(p)
                    f = open(p, 'rb')
                    opened.append(f)
                    files.append(('files', (os.path.basename(p), f, mime or 'application/octet-stream')))
                self.ui_queue.put(("log", f"POST /api/resumes/upload ({len(files)} files)"))
                r = self._api("POST", "/resumes/upload", files=files)
                data = r.json()
                self.ui_queue.put(("append_upload", data))
                ids = data.get('ids') or []
                if ids:
                    self.resume_id_var.set(ids[0])
                    self.action_resume_id.set(ids[0])
            finally:
                for f in opened:
                    try:
                        f.close()
                    except Exception:
                        pass
        self._run_bg(work)

    def run_get_resume(self):
        rid = (self.resume_id_var.get() or '').strip()
        if not rid:
            messagebox.showwarning("Missing", "Enter a Resume ID")
            return
        def work():
            self.ui_queue.put(("log", f"GET /api/resumes/{rid}"))
            r = self._api("GET", f"/resumes/{rid}")
            self.ui_queue.put(("append_upload", r.json()))
        self._run_bg(work)

    def run_search(self):
        q = (self.search_query.get() or '').strip()
        if not q:
            messagebox.showwarning("Missing", "Enter a search query")
            return
        def work():
            self.ui_queue.put(("log", "POST /api/search"))
            r = self._api("POST", "/search", json_body={"query": q, "page_size": 20})
            self.ui_queue.put(("append_search", r.json()))
        self._run_bg(work)

    def run_match(self):
        jd = self.match_jd.get("1.0", END).strip()
        if not jd:
            messagebox.showwarning("Missing", "Enter a job description")
            return
        def work():
            self.ui_queue.put(("log", "POST /api/match"))
            r = self._api("POST", "/match", json_body={"job_description": jd, "top_k": 20})
            self.ui_queue.put(("append_search", r.json()))
        self._run_bg(work)

    def start_chat(self):
        if self.chat_running:
            return
        self.chat_running = True
        self.chat_output.delete("1.0", END)

        def work():
            try:
                payload = {
                    "session_id": self.chat_session.get().strip() or f"tester-{int(time.time())}",
                    "message": self.chat_message.get().strip() or "Hello",
                }
                # Filters JSON is optional
                try:
                    filters_text = self.chat_filters.get("1.0", END).strip()
                    if filters_text:
                        payload["filters"] = json.loads(filters_text)
                except Exception:
                    pass

                self.ui_queue.put(("log", "POST (stream) /api/chat"))
                resp = self._api("POST", "/chat", json_body=payload, stream=True)
                if resp.status_code >= 400:
                    self.ui_queue.put(("append_chat", f"HTTP {resp.status_code}: {resp.text}\n"))
                    return

                for raw in resp.iter_lines(decode_unicode=True):
                    if not self.chat_running:
                        break
                    if raw is None:
                        continue
                    line = raw.strip()
                    if not line:
                        continue
                    # Show raw SSE lines for transparency
                    self.ui_queue.put(("append_chat", line + "\n"))
            except Exception as e:
                self.ui_queue.put(("append_chat", f"Error: {e}\n"))
            finally:
                self.chat_running = False
                self.ui_queue.put(("log", "Chat stream ended"))
        self._run_bg(work)

    def stop_chat(self):
        self.chat_running = False

    def run_status_overview(self):
        def work():
            self.ui_queue.put(("log", "GET /api/status/overview"))
            r = self._api("GET", "/status/overview")
            self.ui_queue.put(("append_status", r.json()))
        self._run_bg(work)

    def run_status_stuck(self):
        def work():
            self.ui_queue.put(("log", "GET /api/status/stuck?minutes=10"))
            r = self._api("GET", "/status/stuck", params={"minutes": 10})
            self.ui_queue.put(("append_status", r.json()))
        self._run_bg(work)

    def run_status_ready(self):
        def work():
            self.ui_queue.put(("log", "GET /api/status/ready"))
            r = self._api("GET", "/status/ready")
            self.ui_queue.put(("append_status", r.json()))
        self._run_bg(work)

    def run_trigger_all_ready(self):
        def work():
            self.ui_queue.put(("log", "POST /api/actions/trigger-all-ready"))
            r = self._api("POST", "/actions/trigger-all-ready", json_body={})
            self.ui_queue.put(("append_status", r.json()))
        self._run_bg(work)

    def run_trigger_one(self):
        rid = (self.action_resume_id.get() or '').strip()
        if not rid:
            messagebox.showwarning("Missing", "Enter a Resume ID")
            return
        def work():
            self.ui_queue.put(("log", f"POST /api/actions/trigger/{rid}"))
            r = self._api("POST", f"/actions/trigger/{rid}", json_body={"force": True})
            self.ui_queue.put(("append_status", r.json()))
        self._run_bg(work)


def main():
    root = Tk()
    # Use ttk theme for nicer look
    try:
        style = ttk.Style()
        if sys.platform.startswith('win'):
            style.theme_use('vista')
        else:
            style.theme_use('clam')
    except Exception:
        pass
    app = RailwayTesterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
