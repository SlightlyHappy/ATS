#!/usr/bin/env python3
"""
CLI and GUI tool to upload resumes to the backend and trigger AI analysis.

Default behavior (no arguments):
- Opens a simple GUI: select one or more resume files, click Upload & Analyze.
- Authenticates automatically as super admin using env or .env.production defaults.
- Stores uploads on server persistent volume and triggers analysis (direct for single file, batch queue for multiple).

Advanced: CLI still supported (same as before) if --file/--dir provided.
"""
import argparse
import os
import sys
import time
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import requests

# Optional GUI (only imported when used)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None

ALLOWED_EXT = {'.pdf', '.doc', '.docx', '.txt'}

# -------------------- Helpers: env/config resolution --------------------

def parse_env_file(env_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            values[k.strip()] = v.strip()
    return values


def resolve_api_base_url(project_root: Optional[Path] = None) -> str:
    # 1) Explicit env
    base = os.getenv('API_BASE_URL')
    if base:
        return base
    # 2) From .env.production RAILWAY_PUBLIC_DOMAIN
    root = project_root or Path(__file__).resolve().parents[1]
    env_vals = parse_env_file(root / '.env.production')
    public_domain = env_vals.get('RAILWAY_PUBLIC_DOMAIN')
    if public_domain:
        scheme = 'https' if not public_domain.startswith(('http://', 'https://')) else ''
        return f"{scheme + '://' if scheme else ''}{public_domain}"
    # 3) Fallback to local dev
    return 'http://localhost:8000'


def resolve_admin_credentials(project_root: Optional[Path] = None) -> Tuple[Optional[str], Optional[str]]:
    # 1) From environment (preferred)
    email = os.getenv('AUTH_EMAIL') or os.getenv('DEFAULT_ADMIN_EMAIL')
    password = os.getenv('AUTH_PASSWORD') or os.getenv('DEFAULT_ADMIN_PASSWORD')
    if email and password:
        return email, password
    # 2) From .env.production
    root = project_root or Path(__file__).resolve().parents[1]
    env_vals = parse_env_file(root / '.env.production')
    email = env_vals.get('DEFAULT_ADMIN_EMAIL') or env_vals.get('ADMIN_EMAIL')
    password = env_vals.get('DEFAULT_ADMIN_PASSWORD') or env_vals.get('ADMIN_PASSWORD')
    return email, password


def build_api_root(base_url: str) -> str:
    base = base_url.rstrip('/')
    if base.endswith('/api') or base.endswith('/api/v1'):
        return base if base.endswith('/v1') else f"{base}/v1"
    return f"{base}/api/v1"

# -------------------- API functions (existing) --------------------

def login(api_root: str, email: str, password: str, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/auth/login"
    resp = requests.post(url, json={"email": email, "password": password}, timeout=30, verify=verify_ssl)
    if resp.status_code != 200:
        raise RuntimeError(f"Login failed: {resp.status_code} {resp.text}")
    return resp.json()


def collect_files_from_dir(directory: Path) -> List[Path]:
    files: List[Path] = []
    for p in directory.rglob('*'):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
            files.append(p)
    return files


def make_zip(files: List[Path]) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    tmp_path = Path(tmp.name)
    tmp.close()
    with zipfile.ZipFile(tmp_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=f.name)
    return tmp_path


def upload_single_queue(api_root: str, token: str, file_path: Path, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/queue/upload"
    headers = {"Authorization": f"Bearer {token}"}
    with open(file_path, 'rb') as fh:
        files = {"file": (file_path.name, fh, "application/octet-stream")}
        resp = requests.post(url, headers=headers, files=files, timeout=120, verify=verify_ssl)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Queue upload failed for {file_path.name}: {resp.status_code} {resp.text}")
    return resp.json()


def upload_batch_zip(api_root: str, token: str, zip_path: Path, batch_name: Optional[str] = None, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/queue/upload/batch"
    headers = {"Authorization": f"Bearer {token}"}
    data = {}
    if batch_name:
        data['batch_name'] = batch_name
    with open(zip_path, 'rb') as fh:
        files = {"zip_file": (zip_path.name, fh, "application/zip")}
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=600, verify=verify_ssl)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Batch upload failed: {resp.status_code} {resp.text}")
    return resp.json()


def upload_single_direct_and_analyze(api_root: str, token: str, file_path: Path, verify_ssl: bool = True) -> Dict:
    up_url = f"{api_root}/resumes"
    headers = {"Authorization": f"Bearer {token}"}
    with open(file_path, 'rb') as fh:
        files = {"file": (file_path.name, fh, "application/octet-stream")}
        resp = requests.post(up_url, headers=headers, files=files, timeout=120, verify=verify_ssl)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Resume upload failed for {file_path.name}: {resp.status_code} {resp.text}")
    up_json = resp.json()
    resume_id = up_json.get('resume_id')
    if not resume_id:
        raise RuntimeError("Missing resume_id from upload response")

    an_url = f"{api_root}/resumes/{resume_id}/analyze"
    resp2 = requests.post(an_url, headers=headers, json={}, timeout=900, verify=verify_ssl)
    if resp2.status_code not in (200, 201):
        raise RuntimeError(f"Analyze failed for {file_path.name}: {resp2.status_code} {resp2.text}")
    return resp2.json()


def poll_batch_completion(api_root: str, token: str, batch_id: str, user_id: str, timeout_s: int = 1800, interval_s: int = 10, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/queue/batch/{batch_id}/status"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": user_id}

    start = time.time()
    last_progress = -1
    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=30, verify=verify_ssl)
        if resp.status_code == 404:
            raise RuntimeError("Batch not found")
        resp.raise_for_status()
        js = resp.json()

        progress = js.get('progress', 0)
        status = js.get('status')
        if progress != last_progress:
            print(f"Batch progress: {progress}% (status={status})")
            last_progress = progress

        if status == 'completed' or progress >= 100:
            print("Batch completed")
            return js

        if time.time() - start > timeout_s:
            raise TimeoutError("Timed out waiting for batch to complete")

        time.sleep(interval_s)


def fetch_latest_analysis_summary(api_root: str, token: str, resume_id: str, verify_ssl: bool = True) -> Optional[Dict]:
    url = f"{api_root}/resumes/{resume_id}/analyses"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": 1, "per_page": 1}
    resp = requests.get(url, headers=headers, params=params, timeout=30, verify=verify_ssl)
    if resp.status_code != 200:
        return None
    data = resp.json()
    items = data.get('analyses', [])
    return items[0] if items else None

# -------------------- GUI --------------------

class SimpleUploaderGUI:
    def __init__(self):
        if tk is None:
            raise RuntimeError('Tkinter not available in this environment')
        self.root = tk.Tk()
        self.root.title('Resume Uploader')
        self.files: List[Path] = []
        self.project_root = Path(__file__).resolve().parents[1]

        self.base_url = resolve_api_base_url(self.project_root)
        self.api_root = build_api_root(self.base_url)
        self.verify_ssl = self.base_url.startswith('https://')

        email, password = resolve_admin_credentials(self.project_root)
        self.email = email
        self.password = password

        # UI
        self.status_var = tk.StringVar(value='Not authenticated')
        tk.Label(self.root, text=f"API: {self.api_root}").pack(padx=8, pady=(8, 0))
        tk.Label(self.root, textvariable=self.status_var, fg='blue').pack(padx=8, pady=(0, 8))

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(padx=8, pady=4, fill='x')
        tk.Button(btn_frame, text='Select Files', command=self.select_files).pack(side='left')
        tk.Button(btn_frame, text='Clear', command=self.clear_files).pack(side='left', padx=6)

        self.listbox = tk.Listbox(self.root, width=80, height=10)
        self.listbox.pack(padx=8, pady=4, fill='both', expand=True)

        self.poll_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.root, text='Poll until batch completes (for multiple files)', variable=self.poll_var).pack(padx=8, pady=4, anchor='w')

        tk.Button(self.root, text='Upload & Analyze', command=self.start_upload).pack(padx=8, pady=(4, 8))

        self.log = tk.Text(self.root, width=80, height=10, state='disabled')
        self.log.pack(padx=8, pady=(0, 8), fill='both', expand=True)

        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.try_login()

    def log_message(self, msg: str):
        self.log.configure(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def try_login(self):
        if not self.email or not self.password:
            self.status_var.set('Missing admin credentials. Set AUTH_EMAIL/AUTH_PASSWORD or .env.production defaults.')
            return
        try:
            auth = login(self.api_root, self.email, self.password, verify_ssl=self.verify_ssl)
            self.token = auth['access_token']
            self.user_id = auth.get('user', {}).get('id')
            self.status_var.set(f"Authenticated as {self.email}")
            self.log_message('Login successful')
        except Exception as e:
            self.status_var.set('Authentication failed')
            self.log_message(f"Login error: {e}")

    def select_files(self):
        filetypes = [('Documents', '*.pdf *.doc *.docx *.txt'), ('All files', '*.*')]
        paths = filedialog.askopenfilenames(title='Select resumes', filetypes=filetypes)
        for p in paths:
            path = Path(p)
            if path.suffix.lower() in ALLOWED_EXT:
                self.files.append(path)
                self.listbox.insert('end', str(path))
        if not paths:
            return
        self.log_message(f"Selected {len(paths)} file(s)")

    def clear_files(self):
        self.files = []
        self.listbox.delete(0, 'end')

    def start_upload(self):
        if not self.token:
            messagebox.showerror('Error', 'Not authenticated. Check credentials and API URL.')
            return
        if not self.files:
            messagebox.showwarning('No files', 'Please select one or more resume files.')
            return
        try:
            if len(self.files) == 1:
                self.log_message(f"Uploading and analyzing {self.files[0].name} (direct mode)...")
                res = upload_single_direct_and_analyze(self.api_root, self.token, self.files[0], verify_ssl=self.verify_ssl)
                self.log_message(f"Done. Analysis ID: {res.get('analysis_id')} Status: {res.get('status')}")
                messagebox.showinfo('Success', 'Single file analyzed successfully')
            else:
                self.log_message(f"Zipping and uploading {len(self.files)} files (batch queue)...")
                zip_path = make_zip(self.files)
                try:
                    res = upload_batch_zip(self.api_root, self.token, zip_path, batch_name='GUI Batch', verify_ssl=self.verify_ssl)
                    self.log_message(f"Batch queued. Batch ID: {res.get('batch_id')}")
                    batch_id = res.get('batch_id')
                    if self.poll_var.get() and batch_id and self.user_id:
                        self.log_message('Polling for batch completion...')
                        status = poll_batch_completion(self.api_root, self.token, batch_id, self.user_id, verify_ssl=self.verify_ssl)
                        self.log_message(f"Batch completed. Status: {status.get('status')} Success: {status.get('successful_analyses')} / {status.get('total_resumes')}")
                        messagebox.showinfo('Batch Complete', 'Batch processing completed')
                    else:
                        messagebox.showinfo('Queued', 'Batch uploaded and queued')
                finally:
                    try:
                        os.unlink(zip_path)
                    except Exception:
                        pass
        except Exception as e:
            self.log_message(f"Error: {e}")
            messagebox.showerror('Upload failed', str(e))

    def run(self):
        self.root.mainloop()

# -------------------- CLI (kept for power users) --------------------

def main():
    # If called without args, launch GUI for simplicity
    if len(sys.argv) == 1:
        if tk is None:
            print('Tkinter GUI not available. Use CLI: --file/--dir', file=sys.stderr)
            sys.exit(1)
        SimpleUploaderGUI().run()
        return

    parser = argparse.ArgumentParser(description="Upload resumes and trigger AI analysis")
    parser.add_argument('--base-url', default=resolve_api_base_url(), help='API base URL (domain, no /api/v1 needed)')
    parser.add_argument('--email', default=resolve_admin_credentials()[0], help='Login email')
    parser.add_argument('--password', default=resolve_admin_credentials()[1], help='Login password')
    parser.add_argument('--file', type=str, help='Path to a single resume file')
    parser.add_argument('--dir', type=str, help='Path to a folder containing resume files')
    parser.add_argument('--mode', choices=['queue', 'direct'], default='queue', help='queue: enqueue processing; direct: analyze synchronously')
    parser.add_argument('--batch-name', type=str, help='Optional batch name (queue mode)')
    parser.add_argument('--poll', action='store_true', help='Poll for completion (queue mode)')
    parser.add_argument('--timeout', type=int, default=1800, help='Polling timeout seconds (queue mode)')
    parser.add_argument('--interval', type=int, default=10, help='Polling interval seconds (queue mode)')
    parser.add_argument('--insecure', action='store_true', help='Disable SSL verification')

    args = parser.parse_args()

    if not args.email or not args.password:
        print('Missing credentials. Provide --email and --password or set AUTH_EMAIL/AUTH_PASSWORD env vars.', file=sys.stderr)
        sys.exit(1)

    verify_ssl = not args.insecure if args.base_url.startswith('https://') else False

    api_root = build_api_root(args.base_url)

    # Authenticate
    auth = login(api_root, args.email, args.password, verify_ssl=verify_ssl)
    token = auth['access_token']
    user = auth.get('user', {})
    user_id = user.get('id')
    if not user_id:
        me = requests.get(f"{api_root}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=30, verify=verify_ssl)
        me.raise_for_status()
        user_id = me.json().get('id')

    # Determine inputs
    files: List[Path] = []
    if args.file:
        p = Path(args.file)
        if not p.exists() or not p.is_file():
            print(f"File not found: {p}", file=sys.stderr)
            sys.exit(1)
        if p.suffix.lower() not in ALLOWED_EXT:
            print(f"Unsupported extension {p.suffix}. Allowed: {sorted(ALLOWED_EXT)}", file=sys.stderr)
            sys.exit(1)
        files = [p]
    elif args.dir:
        d = Path(args.dir)
        if not d.exists() or not d.is_dir():
            print(f"Directory not found: {d}", file=sys.stderr)
            sys.exit(1)
        files = collect_files_from_dir(d)
        if not files:
            print("No supported files found in directory.")
            sys.exit(1)
    else:
        # No inputs provided via CLI -> launch GUI to keep it simple
        if tk is None:
            print('No --file/--dir provided and Tkinter GUI not available.', file=sys.stderr)
            sys.exit(1)
        SimpleUploaderGUI().run()
        return

    if args.mode == 'direct':
        if len(files) != 1:
            print("Direct mode supports a single file. Use --file.", file=sys.stderr)
            sys.exit(1)
        result = upload_single_direct_and_analyze(api_root, token, files[0], verify_ssl=verify_ssl)
        print("Analyze result:", result)
        sys.exit(0)

    # Queue mode
    if len(files) == 1:
        res = upload_single_queue(api_root, token, files[0], verify_ssl=verify_ssl)
        print("Queued:", res)
        sys.exit(0)

    # Batch: make zip and upload
    zip_path = make_zip(files)
    try:
        res = upload_batch_zip(api_root, token, zip_path, batch_name=args.batch_name, verify_ssl=verify_ssl)
        print("Batch queued:", res)
        batch_id = res.get('batch_id')
        resume_ids = res.get('resume_ids', [])

        if args.poll and batch_id and user_id:
            status = poll_batch_completion(api_root, token, batch_id, user_id, timeout_s=args.timeout, interval_s=args.interval, verify_ssl=verify_ssl)
            print("Final batch status:", status)
            # Optionally fetch a quick summary for each resume
            summaries = []
            for rid in resume_ids:
                summary = fetch_latest_analysis_summary(api_root, token, rid, verify_ssl=verify_ssl)
                if summary:
                    summaries.append({"resume_id": rid, "overall_score": summary.get('overall_score'), "status": summary.get('status')})
            if summaries:
                print("Analysis summaries:", summaries)
    finally:
        try:
            os.unlink(zip_path)
        except Exception:
            pass


if __name__ == '__main__':
    main()
