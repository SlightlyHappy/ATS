#!/usr/bin/env python3
"""
Visual Resume & Analysis Viewer (GUI)

- Authenticates automatically as super admin using env or .env.production defaults
- Lists resumes and shows their analyses
- View resume text, trigger analysis, and inspect agent results

Run: python scripts/resume_viewer.py
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Optional GUI
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:
    tk = None

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
    base = os.getenv('API_BASE_URL')
    if base:
        return base
    root = project_root or Path(__file__).resolve().parents[1]
    env_vals = parse_env_file(root / '.env.production')
    public_domain = env_vals.get('RAILWAY_PUBLIC_DOMAIN')
    if public_domain:
        if public_domain.startswith(('http://', 'https://')):
            return public_domain
        return f"https://{public_domain}"
    return 'http://localhost:8000'


def resolve_admin_credentials(project_root: Optional[Path] = None) -> Tuple[Optional[str], Optional[str]]:
    email = os.getenv('AUTH_EMAIL') or os.getenv('DEFAULT_ADMIN_EMAIL')
    password = os.getenv('AUTH_PASSWORD') or os.getenv('DEFAULT_ADMIN_PASSWORD')
    if email and password:
        return email, password
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

# -------------------- API helpers --------------------

def login(api_root: str, email: str, password: str, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/auth/login"
    resp = requests.post(url, json={"email": email, "password": password}, timeout=30, verify=verify_ssl)
    if resp.status_code != 200:
        raise RuntimeError(f"Login failed: {resp.status_code} {resp.text}")
    return resp.json()


def list_resumes(api_root: str, token: str, page: int = 1, per_page: int = 50, status: Optional[str] = None, user_id: Optional[str] = None, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/resumes"
    headers = {"Authorization": f"Bearer {token}"}
    params: Dict[str, object] = {"page": page, "per_page": per_page}
    if status:
        params["status"] = status
    if user_id:
        params["user_id"] = user_id
    resp = requests.get(url, headers=headers, params=params, timeout=30, verify=verify_ssl)
    resp.raise_for_status()
    return resp.json()


def get_resume(api_root: str, token: str, resume_id: str, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/resumes/{resume_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30, verify=verify_ssl)
    resp.raise_for_status()
    return resp.json()


def get_resume_text(api_root: str, token: str, resume_id: str, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/resumes/{resume_id}/text"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=60, verify=verify_ssl)
    resp.raise_for_status()
    return resp.json()


def list_resume_analyses(api_root: str, token: str, resume_id: str, page: int = 1, per_page: int = 10, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/resumes/{resume_id}/analyses"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": page, "per_page": per_page}
    resp = requests.get(url, headers=headers, params=params, timeout=30, verify=verify_ssl)
    resp.raise_for_status()
    return resp.json()


def get_analysis(api_root: str, token: str, analysis_id: str, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/analyses/{analysis_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=60, verify=verify_ssl)
    resp.raise_for_status()
    return resp.json()


def analyze_resume_now(api_root: str, token: str, resume_id: str, verify_ssl: bool = True) -> Dict:
    url = f"{api_root}/resumes/{resume_id}/analyze"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, headers=headers, json={}, timeout=900, verify=verify_ssl)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Analyze failed: {resp.status_code} {resp.text}")
    return resp.json()

# -------------------- GUI --------------------

class ResumeAnalysisViewer:
    def __init__(self):
        if tk is None:
            raise RuntimeError('Tkinter not available in this environment')

        self.root = tk.Tk()
        self.root.title('Resume & Analysis Viewer')
        self.project_root = Path(__file__).resolve().parents[1]

        # Auth/setup
        self.base_url = resolve_api_base_url(self.project_root)
        self.api_root = build_api_root(self.base_url)
        self.verify_ssl = self.base_url.startswith('https://')
        self.email, self.password = resolve_admin_credentials(self.project_root)
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None

        # State
        self.current_page = 1
        self.per_page = 50
        self.current_status_filter: Optional[str] = None
        self.selected_resume_id: Optional[str] = None

        # UI
        self._build_ui()
        self._login_and_load()

    # ---- UI construction ----
    def _build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill='x', padx=8, pady=6)

        tk.Label(top, text=f"API: {self.api_root}").pack(side='left')
        self.status_var = tk.StringVar(value='Not authenticated')
        tk.Label(top, textvariable=self.status_var, fg='blue').pack(side='right')

        # Controls
        ctl = tk.Frame(self.root)
        ctl.pack(fill='x', padx=8, pady=(0, 6))
        tk.Button(ctl, text='Refresh', command=self.refresh_resumes).pack(side='left')

        tk.Label(ctl, text='Status:').pack(side='left', padx=(12, 4))
        self.status_filter = ttk.Combobox(ctl, values=['', 'pending', 'text_extracted', 'failed'], width=18)
        self.status_filter.set('')
        self.status_filter.pack(side='left')
        tk.Button(ctl, text='Apply', command=self.apply_filter).pack(side='left', padx=(4, 0))

        # Paned window
        paned = ttk.Panedwindow(self.root, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=8, pady=6)

        # Left: Resumes list
        left = tk.Frame(paned)
        self.resumes_tree = ttk.Treeview(left, columns=('filename', 'status', 'created', 'size', 'id'), show='headings', height=18)
        for col, w in [('filename', 260), ('status', 120), ('created', 160), ('size', 80), ('id', 280)]:
            self.resumes_tree.heading(col, text=col.title())
            self.resumes_tree.column(col, width=w, anchor='w')
        self.resumes_tree.bind('<<TreeviewSelect>>', self.on_resume_select)
        yscroll = ttk.Scrollbar(left, orient='vertical', command=self.resumes_tree.yview)
        self.resumes_tree.configure(yscrollcommand=yscroll.set)
        self.resumes_tree.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')

        pagers = tk.Frame(left)
        pagers.pack(fill='x', pady=(4, 0))
        tk.Button(pagers, text='Prev', command=self.prev_page).pack(side='left')
        self.page_var = tk.StringVar(value='Page 1')
        tk.Label(pagers, textvariable=self.page_var).pack(side='left', padx=8)
        tk.Button(pagers, text='Next', command=self.next_page).pack(side='left')

        paned.add(left, weight=1)

        # Right: Details
        right = tk.Frame(paned)

        # Resume info and actions
        info = tk.Frame(right)
        info.pack(fill='x')
        self.resume_title = tk.StringVar(value='Select a resume to view details')
        tk.Label(info, textvariable=self.resume_title, font=('Segoe UI', 10, 'bold')).pack(side='left')

        actions = tk.Frame(right)
        actions.pack(fill='x', pady=(4, 6))
        tk.Button(actions, text='View Text', command=self.view_text).pack(side='left')
        tk.Button(actions, text='Analyze Now', command=self.analyze_now).pack(side='left', padx=6)

        # Analyses list
        tk.Label(right, text='Analyses:').pack(anchor='w')
        ana_frame = tk.Frame(right)
        ana_frame.pack(fill='x')
        self.analyses_tree = ttk.Treeview(ana_frame, columns=('id', 'status', 'score', 'created'), show='headings', height=6)
        for col, w in [('id', 260), ('status', 120), ('score', 80), ('created', 160)]:
            self.analyses_tree.heading(col, text=col.title())
            self.analyses_tree.column(col, width=w, anchor='w')
        self.analyses_tree.bind('<<TreeviewSelect>>', self.on_analysis_select)
        ay = ttk.Scrollbar(ana_frame, orient='vertical', command=self.analyses_tree.yview)
        self.analyses_tree.configure(yscrollcommand=ay.set)
        self.analyses_tree.pack(side='left', fill='x', expand=True)
        ay.pack(side='right', fill='y')

        # Notebook for details
        nb = ttk.Notebook(right)
        nb.pack(fill='both', expand=True, pady=(6, 0))

        self.summary_txt = tk.Text(nb, wrap='word')
        self.summary_txt.configure(state='disabled')
        nb.add(self.summary_txt, text='Summary')

        self.strengths_txt = tk.Text(nb, wrap='word'); self.strengths_txt.configure(state='disabled')
        nb.add(self.strengths_txt, text='Strengths')
        self.weaknesses_txt = tk.Text(nb, wrap='word'); self.weaknesses_txt.configure(state='disabled')
        nb.add(self.weaknesses_txt, text='Weaknesses')
        self.recommendations_txt = tk.Text(nb, wrap='word'); self.recommendations_txt.configure(state='disabled')
        nb.add(self.recommendations_txt, text='Recommendations')

        self.agents_txt = tk.Text(nb, wrap='word'); self.agents_txt.configure(state='disabled')
        nb.add(self.agents_txt, text='Agent Results')

        paned.add(right, weight=2)

    # ---- Auth and data load ----
    def _login_and_load(self):
        if not self.email or not self.password:
            self.status_var.set('Missing admin credentials. Set AUTH_EMAIL/AUTH_PASSWORD or .env.production defaults.')
            return
        try:
            auth = login(self.api_root, self.email, self.password, verify_ssl=self.verify_ssl)
            self.token = auth['access_token']
            self.user_id = auth.get('user', {}).get('id')
            self.status_var.set(f"Authenticated as {self.email}")
            self.refresh_resumes()
        except Exception as e:
            self.status_var.set('Authentication failed')
            messagebox.showerror('Login failed', str(e))

    # ---- Resume list ----
    def refresh_resumes(self):
        self.resumes_tree.delete(*self.resumes_tree.get_children())
        try:
            data = list_resumes(self.api_root, self.token, page=self.current_page, per_page=self.per_page, status=self.current_status_filter, verify_ssl=self.verify_ssl)
            resumes = data.get('resumes', [])
            pag = data.get('pagination', {})
            self.page_var.set(f"Page {pag.get('page', self.current_page)} / {pag.get('pages', '?')}")
            for r in resumes:
                rid = r.get('id') or r.get('resume_id') or ''
                created = r.get('created_at') or ''
                size = r.get('file_size')
                size_str = f"{size/1024:.1f} KB" if isinstance(size, (int, float)) else ''
                self.resumes_tree.insert('', 'end', iid=rid, values=(r.get('original_filename') or r.get('filename'), r.get('processing_status'), created, size_str, rid))
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load resumes: {e}')

    def apply_filter(self):
        val = self.status_filter.get().strip()
        self.current_status_filter = val or None
        self.current_page = 1
        self.refresh_resumes()

    def next_page(self):
        self.current_page += 1
        self.refresh_resumes()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_resumes()

    # ---- Selection handlers ----
    def on_resume_select(self, _evt):
        sel = self.resumes_tree.selection()
        if not sel:
            return
        rid = sel[0]
        self.selected_resume_id = rid
        try:
            info = get_resume(self.api_root, self.token, rid, verify_ssl=self.verify_ssl)
            title = f"{info.get('original_filename') or info.get('filename')} — {info.get('processing_status')}"
            self.resume_title.set(title)
            self.load_analyses(rid)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load resume: {e}')

    def load_analyses(self, resume_id: str):
        self.analyses_tree.delete(*self.analyses_tree.get_children())
        self._clear_analysis_texts()
        try:
            data = list_resume_analyses(self.api_root, self.token, resume_id, page=1, per_page=10, verify_ssl=self.verify_ssl)
            for a in data.get('analyses', []):
                aid = a.get('id')
                status = a.get('status')
                score = a.get('overall_score')
                created = a.get('created_at')
                self.analyses_tree.insert('', 'end', iid=aid, values=(aid, status, score, created))
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load analyses: {e}')

    def on_analysis_select(self, _evt):
        sel = self.analyses_tree.selection()
        if not sel:
            return
        aid = sel[0]
        try:
            info = get_analysis(self.api_root, self.token, aid, verify_ssl=self.verify_ssl)
            self._fill_analysis_texts(info)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load analysis: {e}')

    # ---- Actions ----
    def view_text(self):
        if not self.selected_resume_id:
            return
        try:
            data = get_resume_text(self.api_root, self.token, self.selected_resume_id, verify_ssl=self.verify_ssl)
            txt = data.get('text') or ''
            self._show_text_window('Resume Text', txt)
        except requests.HTTPError as e:
            messagebox.showwarning('No text', f'{e}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to get text: {e}')

    def analyze_now(self):
        if not self.selected_resume_id:
            return
        if not messagebox.askyesno('Analyze', 'Run analysis now? This will consume credits.'):
            return
        try:
            res = analyze_resume_now(self.api_root, self.token, self.selected_resume_id, verify_ssl=self.verify_ssl)
            messagebox.showinfo('Analysis', f"Analysis complete. Overall score: {res.get('overall_score')}")
            self.load_analyses(self.selected_resume_id)
        except Exception as e:
            messagebox.showerror('Error', f'Analyze failed: {e}')

    # ---- Helpers ----
    def _show_text_window(self, title: str, content: str):
        win = tk.Toplevel(self.root)
        win.title(title)
        txt = tk.Text(win, wrap='word')
        y = ttk.Scrollbar(win, orient='vertical', command=txt.yview)
        txt.configure(yscrollcommand=y.set)
        txt.pack(side='left', fill='both', expand=True)
        y.pack(side='right', fill='y')
        txt.insert('1.0', content)

    def _clear_analysis_texts(self):
        for t in (self.summary_txt, self.strengths_txt, self.weaknesses_txt, self.recommendations_txt, self.agents_txt):
            t.configure(state='normal'); t.delete('1.0', 'end'); t.configure(state='disabled')

    def _fill_analysis_texts(self, a: Dict):
        def set_text(widget, text: str):
            widget.configure(state='normal'); widget.delete('1.0', 'end'); widget.insert('1.0', text); widget.configure(state='disabled')

        # Summary
        lines = [
            f"Analysis ID: {a.get('id')}",
            f"Status: {a.get('status')}",
            f"Overall Score: {a.get('overall_score')}",
            f"Processing Time: {a.get('processing_time')}s",
            f"Created: {a.get('created_at')}  Completed: {a.get('completed_at')}"
        ]
        if a.get('scores_breakdown'):
            lines.append('Scores Breakdown:')
            try:
                for k, v in a['scores_breakdown'].items():
                    lines.append(f"  - {k}: {v.get('score')}")
            except Exception:
                lines.append(json.dumps(a['scores_breakdown'], indent=2))
        set_text(self.summary_txt, "\n".join(lines))

        # Strengths/Weaknesses/Recommendations
        def fmt_list(v):
            if isinstance(v, list):
                return "\n".join(f"• {x}" for x in v)
            if isinstance(v, dict):
                return json.dumps(v, indent=2)
            return str(v or '')

        set_text(self.strengths_txt, fmt_list(a.get('strengths')))
        set_text(self.weaknesses_txt, fmt_list(a.get('weaknesses')))
        set_text(self.recommendations_txt, fmt_list(a.get('recommendations')))

        # Agent results
        agents = a.get('agent_results') or {}
        if agents and isinstance(agents, dict):
            lines = []
            for name, result in agents.items():
                lines.append(f"[{name}]")
                if isinstance(result, (dict, list)):
                    lines.append(json.dumps(result, indent=2))
                else:
                    lines.append(str(result))
                lines.append('')
            set_text(self.agents_txt, "\n".join(lines))
        else:
            set_text(self.agents_txt, 'No agent results available')

    def run(self):
        self.root.mainloop()


def main():
    if tk is None:
        print('Tkinter GUI not available. Please run on a system with Tk.', file=sys.stderr)
        sys.exit(1)
    ResumeAnalysisViewer().run()


if __name__ == '__main__':
    main()
