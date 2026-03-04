import os
import subprocess
import shutil
import json
import uuid
from flask import Flask, render_template, request, jsonify, send_file, abort
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max upload

PROJECTS_DIR = os.path.join(os.path.dirname(__file__), 'projects')
DEFAULT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'default_template.tex')

os.makedirs(PROJECTS_DIR, exist_ok=True)

DEFAULT_TEMPLATE = r"""\documentclass[12pt, a4paper]{article}

% --- Packages ---------------------------------------------------------------
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[english]{babel}
\usepackage{geometry}
\geometry{margin=2.5cm}

\usepackage{amsmath, amssymb, amsfonts}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{titlesec}

% --- Header / Footer --------------------------------------------------------
\pagestyle{fancy}
\fancyhf{}
\rhead{\textcolor{gray}{\small %%PROJECT_NAME%%}}
\lhead{\textcolor{gray}{\small \leftmark}}
\cfoot{\thepage}

% --- Title formatting -------------------------------------------------------
\titleformat{\section}{\large\bfseries\color{black}}{\thesection}{1em}{}
\titleformat{\subsection}{\normalsize\bfseries}{}{0em}{}

% --- Hyperlink colors -------------------------------------------------------
\hypersetup{
    colorlinks = true,
    linkcolor  = blue!60!black,
    urlcolor   = blue!70!black,
    citecolor  = green!50!black
}

% ============================================================================
\begin{document}

\begin{titlepage}
    \centering
    \vspace*{3cm}
    {{\Huge\bfseries %%PROJECT_NAME%%\par}}
    \vspace{1cm}
    {\large\itshape A LaTeX Document\par}
    \vspace{2cm}
    {\large Author Name\par}
    \vspace{0.5cm}
    {\normalsize \today\par}
    \vfill
\end{titlepage}

\tableofcontents
\newpage

% --- Introduction -----------------------------------------------------------
\section{Introduction}

Welcome to your new \LaTeX{} project! This template provides a clean starting
point with useful packages already included.

You can write \textbf{bold text}, \textit{italic text}, or
\textcolor{blue}{colored text}. Here is an inline equation: $E = mc^2$.

% --- Background -------------------------------------------------------------
\section{Background}

\subsection{Mathematics}

Display equations are easy:
\begin{equation}
    \int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
\end{equation}

\subsection{Lists}

\begin{itemize}[leftmargin=*]
    \item First item
    \item Second item with \href{https://www.latex-project.org}{\LaTeX{} link}
    \item Third item
\end{itemize}

\begin{enumerate}
    \item Numbered item one
    \item Numbered item two
\end{enumerate}

% --- Methods ----------------------------------------------------------------
\section{Methods}

\subsection{Tables}

\begin{table}[h]
    \centering
    \caption{A sample table}
    \begin{tabular}{lcc}
        \toprule
        \textbf{Name} & \textbf{Value} & \textbf{Unit} \\
        \midrule
        Alpha & 1.00 & m/s \\
        Beta  & 2.45 & kg  \\
        Gamma & 0.03 & s   \\
        \bottomrule
    \end{tabular}
\end{table}

% --- Conclusion -------------------------------------------------------------
\section{Conclusion}

Edit this document to suit your needs. Happy writing!

\end{document}
"""


def get_projects_meta():
    meta_file = os.path.join(PROJECTS_DIR, '_meta.json')
    if os.path.exists(meta_file):
        with open(meta_file, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_projects_meta(meta):
    meta_file = os.path.join(PROJECTS_DIR, '_meta.json')
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)


@app.route('/')
def index():
    meta = get_projects_meta()
    projects = []
    for pid, info in meta.items():
        projects.append({
            'id': pid,
            'name': info.get('name', 'Untitled'),
            'created': info.get('created', ''),
            'modified': info.get('modified', '')
        })
    projects.sort(key=lambda x: x['modified'], reverse=True)
    return render_template('index.html', projects=projects)


@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    name = data.get('name', 'Untitled Project').strip() or 'Untitled Project'
    pid = str(uuid.uuid4())[:8]
    project_dir = os.path.join(PROJECTS_DIR, pid)
    os.makedirs(project_dir, exist_ok=True)

    # Write main.tex from default template, injecting the project name
    tex_path = os.path.join(project_dir, 'main.tex')
    tex_content = DEFAULT_TEMPLATE.replace('%%PROJECT_NAME%%', name)
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    meta = get_projects_meta()
    meta[pid] = {'name': name, 'created': now, 'modified': now}
    save_projects_meta(meta)

    return jsonify({'id': pid, 'name': name})


@app.route('/api/projects/<pid>', methods=['DELETE'])
def delete_project(pid):
    project_dir = os.path.join(PROJECTS_DIR, pid)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    meta = get_projects_meta()
    meta.pop(pid, None)
    save_projects_meta(meta)
    return jsonify({'ok': True})


@app.route('/api/projects/<pid>/rename', methods=['POST'])
def rename_project(pid):
    data = request.json
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400
    meta = get_projects_meta()
    if pid not in meta:
        return jsonify({'error': 'Not found'}), 404
    meta[pid]['name'] = name
    save_projects_meta(meta)
    return jsonify({'ok': True})


@app.route('/editor/<pid>')
def editor(pid):
    meta = get_projects_meta()
    if pid not in meta:
        abort(404)
    project = meta[pid]
    tex_path = os.path.join(PROJECTS_DIR, pid, 'main.tex')
    content = ''
    if os.path.exists(tex_path):
        with open(tex_path, encoding='utf-8') as f:
            content = f.read()
    return render_template('editor.html', pid=pid, project_name=project['name'], content=content)


@app.route('/api/projects/<pid>/save', methods=['POST'])
def save_file(pid):
    data = request.json
    content = data.get('content', '')
    tex_path = os.path.join(PROJECTS_DIR, pid, 'main.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(content)
    meta = get_projects_meta()
    if pid in meta:
        meta[pid]['modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_projects_meta(meta)
    return jsonify({'ok': True})


@app.route('/api/projects/<pid>/compile', methods=['POST'])
def compile_project(pid):
    # Optionally save content first
    data = request.json or {}
    content = data.get('content')
    project_dir = os.path.join(PROJECTS_DIR, pid)
    tex_path = os.path.join(project_dir, 'main.tex')

    if content is not None:
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(content)

    if not os.path.exists(tex_path):
        return jsonify({'success': False, 'log': 'main.tex not found'}), 404

    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', project_dir, tex_path],
            capture_output=True, text=True, timeout=60,
            encoding='utf-8', errors='replace'
        )
        # Run twice for TOC / references
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', project_dir, tex_path],
            capture_output=True, text=True, timeout=60,
            encoding='utf-8', errors='replace'
        )

        pdf_path = os.path.join(project_dir, 'main.pdf')
        stdout = result.stdout or ''
        stderr = result.stderr or ''
        if os.path.exists(pdf_path):
            return jsonify({'success': True, 'log': stdout + stderr})
        else:
            return jsonify({'success': False, 'log': stdout + stderr})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'log': 'Compilation timed out after 60 seconds.'})
    except FileNotFoundError:
        return jsonify({'success': False, 'log': 'pdflatex not found. Please install TeX Live: sudo apt install texlive-full'})


@app.route('/api/projects/<pid>/pdf')
def get_pdf(pid):
    pdf_path = os.path.join(PROJECTS_DIR, pid, 'main.pdf')
    if not os.path.exists(pdf_path):
        abort(404)
    return send_file(pdf_path, mimetype='application/pdf')


# ── Image routes ─────────────────────────────────────────────────────────────

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'pdf', 'eps', 'svg'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@app.route('/api/projects/<pid>/images', methods=['GET'])
def list_images(pid):
    images_dir = os.path.join(PROJECTS_DIR, pid, 'images')
    os.makedirs(images_dir, exist_ok=True)
    files = []
    for fname in sorted(os.listdir(images_dir)):
        fpath = os.path.join(images_dir, fname)
        if os.path.isfile(fpath) and allowed_image(fname):
            size = os.path.getsize(fpath)
            files.append({'name': fname, 'size': size})
    return jsonify(files)


@app.route('/api/projects/<pid>/images', methods=['POST'])
def upload_image(pid):
    project_dir = os.path.join(PROJECTS_DIR, pid)
    if not os.path.exists(project_dir):
        abort(404)
    images_dir = os.path.join(project_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    uploaded = []
    errors = []
    for f in request.files.getlist('file'):
        if f.filename == '':
            continue
        filename = os.path.basename(f.filename).replace(' ', '_')
        if not allowed_image(filename):
            errors.append(f'{filename}: unsupported format')
            continue
        dest = os.path.join(images_dir, filename)
        if os.path.exists(dest):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(images_dir, f'{base}_{counter}{ext}')):
                counter += 1
            filename = f'{base}_{counter}{ext}'
            dest = os.path.join(images_dir, filename)
        f.save(dest)
        size = os.path.getsize(dest)
        uploaded.append({'name': filename, 'size': size})

    return jsonify({'uploaded': uploaded, 'errors': errors})


@app.route('/api/projects/<pid>/images/<filename>', methods=['DELETE'])
def delete_image(pid, filename):
    filename = os.path.basename(filename)
    img_path = os.path.join(PROJECTS_DIR, pid, 'images', filename)
    if os.path.exists(img_path):
        os.remove(img_path)
        return jsonify({'ok': True})
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/projects/<pid>/images/<filename>', methods=['GET'])
def serve_image(pid, filename):
    filename = os.path.basename(filename)
    images_dir = os.path.join(PROJECTS_DIR, pid, 'images')
    img_path = os.path.join(images_dir, filename)
    if not os.path.exists(img_path):
        abort(404)
    return send_file(img_path)


# ── Export project as ZIP ─────────────────────────────────────────────────────

@app.route('/api/projects/<pid>/export')
def export_project(pid):
    import zipfile, io
    meta = get_projects_meta()
    if pid not in meta:
        abort(404)
    project_dir = os.path.join(PROJECTS_DIR, pid)
    project_name = meta[pid].get('name', 'project').replace(' ', '_')

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(project_dir):
            # skip auxiliary latex build files
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, project_dir)
                zf.write(fpath, arcname)
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{project_name}.zip'
    )


# ── Import project from ZIP or RAR ───────────────────────────────────────────

@app.route('/api/projects/import', methods=['POST'])
def import_project():
    import zipfile, io, traceback

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    f = request.files['file']
    name = request.form.get('name', '').strip()
    filename = f.filename or ''
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext not in ('zip', 'rar'):
        return jsonify({'error': 'Only .zip and .rar files are supported'}), 400

    if not name:
        name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').strip() or 'Imported Project'

    pid = str(uuid.uuid4())[:8]
    project_dir = os.path.join(PROJECTS_DIR, pid)
    os.makedirs(project_dir, exist_ok=True)

    try:
        raw = f.read()

        # ── Extract ────────────────────────────────────────────────────────
        if ext == 'zip':
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for member in zf.infolist():
                    # Normalize path: replace backslashes (Windows zips), strip leading slashes
                    member_path = member.filename.replace('\\', '/')
                    # Skip directory entries (end with /)
                    if member_path.endswith('/'):
                        continue
                    # Block path traversal
                    parts = [p for p in member_path.split('/') if p and p != '.']
                    if any(p == '..' for p in parts):
                        continue
                    safe_rel = os.path.join(*parts)
                    dest = os.path.join(project_dir, safe_rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open(member) as src, open(dest, 'wb') as dst:
                        dst.write(src.read())

        elif ext == 'rar':
            tmp_rar = os.path.join(project_dir, '_import.rar')
            with open(tmp_rar, 'wb') as tmp:
                tmp.write(raw)
            result = subprocess.run(
                ['unrar', 'x', '-o+', tmp_rar, project_dir + os.sep],
                capture_output=True, text=True
            )
            os.remove(tmp_rar)
            if result.returncode != 0:
                shutil.rmtree(project_dir, ignore_errors=True)
                return jsonify({
                    'error': 'RAR extraction failed. Make sure unrar is installed:\n  sudo apt install unrar\n\nDetails: ' + result.stderr
                }), 500

        # ── Flatten single top-level folder ───────────────────────────────
        # e.g. archive contains myproject/ with everything inside
        entries = [e for e in os.listdir(project_dir)]
        if len(entries) == 1:
            inner = os.path.join(project_dir, entries[0])
            if os.path.isdir(inner):
                for item in os.listdir(inner):
                    src_path = os.path.join(inner, item)
                    dst_path = os.path.join(project_dir, item)
                    # avoid collision
                    if os.path.exists(dst_path):
                        dst_path = os.path.join(project_dir, '_' + item)
                    shutil.move(src_path, dst_path)
                shutil.rmtree(inner, ignore_errors=True)

        # ── Find / create main.tex ─────────────────────────────────────────
        tex_path = os.path.join(project_dir, 'main.tex')
        if not os.path.exists(tex_path):
            # Search entire project tree for any .tex file
            tex_files = []
            for root, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for fn in files:
                    if fn.lower().endswith('.tex'):
                        tex_files.append(os.path.join(root, fn))

            if tex_files:
                # Prefer files not named beamer/slides and pick the largest (likely the main doc)
                tex_files.sort(key=lambda p: os.path.getsize(p), reverse=True)
                chosen = tex_files[0]
                if os.path.abspath(chosen) != os.path.abspath(tex_path):
                    shutil.copy(chosen, tex_path)
            else:
                # No .tex at all — write default template
                with open(tex_path, 'w', encoding='utf-8') as fp:
                    fp.write(DEFAULT_TEMPLATE.replace('%%PROJECT_NAME%%', name))

        # ── Save metadata (this is the critical step) ──────────────────────
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        meta = get_projects_meta()
        meta[pid] = {'name': name, 'created': now, 'modified': now}
        save_projects_meta(meta)

        return jsonify({'id': pid, 'name': name, 'tex_found': os.path.exists(tex_path)})

    except Exception as e:
        # Clean up the failed project folder
        shutil.rmtree(project_dir, ignore_errors=True)
        err_detail = traceback.format_exc()
        print('Import error:\n', err_detail)
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)