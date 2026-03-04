# LaTeX Studio

A self-hosted, Overleaf-style LaTeX editor that runs on your own machine.
Split-pane interface: syntax-highlighted editor on the left, compiled PDF viewer on the right.

---

## Quick Start with Docker (Recommended)

```bash
docker compose up --build
```

Then open: **http://localhost:5000**

> First build takes 15–30 minutes (downloads TeX Live ~5 GB). Subsequent builds are instant.

---

## Requirements (without Docker)

| Requirement | Notes |
|---|---|
| Python 3.9+ | 3.11 recommended |
| pdflatex | Provided by TeX Live |
| unrar-free *(optional)* | Only needed for `.rar` import |

### Install TeX Live

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install texlive-full lmodern
```

**Windows:**
Download and install [MiKTeX](https://miktex.org/download) or [TeX Live for Windows](https://tug.org/texlive/).
Make sure `pdflatex` is in your PATH.

### Install unrar (optional, for .rar import)

**Ubuntu / Debian:**
```bash
sudo apt install unrar-free
```

**Windows:**
Install WinRAR or 7-Zip and add `unrar.exe` to your PATH.

---

## Installation (without Docker)

```bash
# 1. Enter the project folder
cd latex-studio

# 2. Create a virtual environment (recommended)
python -m venv venv

# Activate on Linux/macOS:
source venv/bin/activate

# Activate on Windows:
venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run
python app.py
```

Open your browser at **http://localhost:5000**.

To access from other devices on your network:
```
http://<your-machine-ip>:5000
```

---

## Docker

### Option A — Docker Compose (recommended)

```bash
# Build and start
docker compose up --build

# Run in the background
docker compose up --build -d

# Stop
docker compose down

# Stream logs
docker compose logs -f
```

### Option B — Plain Docker

```bash
# Build the image
docker build -t latex-studio .

# Run (Linux/macOS)
docker run -d \
  --name latex-studio \
  -p 5000:5000 \
  -v $(pwd)/projects:/app/projects \
  --restart unless-stopped \
  latex-studio

# Run (Windows PowerShell)
docker run -d `
  --name latex-studio `
  -p 5000:5000 `
  -v ${PWD}/projects:/app/projects `
  --restart unless-stopped `
  latex-studio
```

### Data Persistence

Projects are stored in the `projects/` folder on your **host machine** (mounted as a Docker volume).
Your data survives container restarts, rebuilds, and image updates.

```
latex-studio/
└── projects/           ← lives on your host, not inside the container
    ├── _meta.json
    └── <project-id>/
        ├── main.tex
        ├── main.pdf
        └── images/
```

### Useful Docker Commands

| Command | Description |
|---|---|
| `docker compose up --build -d` | Build and start in background |
| `docker compose down` | Stop and remove container |
| `docker compose logs -f` | Stream live logs |
| `docker compose restart` | Restart the container |
| `docker exec -it latex-studio bash` | Open a shell inside the container |
| `docker images` | List built images |
| `docker rmi latex-studio` | Delete the image (forces full rebuild) |

---

## Features

### Dashboard
- Create new projects (default template uses your project name as title)
- Import existing projects from `.zip` or `.rar` archives (drag-and-drop)
- Export any project as a `.zip` download
- Rename and delete projects

### Editor
- LaTeX syntax highlighting (CodeMirror, Dracula theme)
- Toolbar: bold, italic, sections, equations, lists, tables, figures
- Auto-save — triggers 2 seconds after you stop typing
- Manual save: `Ctrl+S`
- Compile: `Ctrl+Enter` or the green **Compile PDF** button
- Resizable split pane — drag the divider between editor and PDF
- Color-coded compilation log (errors in red, warnings in yellow)
- Inline PDF viewer with refresh and download buttons

### Import / Export
- Import `.zip` or `.rar` — drag-and-drop or click to browse
- Flat and single-folder archives handled automatically
- Largest `.tex` file in the archive promoted to `main.tex`
- Export any project as `.zip` from the dashboard card

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + S` | Save |
| `Ctrl + Enter` | Compile PDF |
| `Ctrl + /` | Toggle comment |

---

## Project Structure

```
latex-studio/
│
├── app.py                  # Flask backend — all routes and logic
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Files excluded from Docker build
├── README.md
│
├── templates/
│   ├── index.html          # Project dashboard
│   └── editor.html         # Split-pane editor + PDF viewer
│
└── projects/               # Created automatically on first run
    ├── _meta.json          # Project registry (names, dates, IDs)
    │
    ├── <project-id>/       # One folder per project (8-char UUID)
    │   ├── main.tex        # LaTeX source (editable in browser)
    │   ├── main.pdf        # Generated after first compile
    │   └── images/         # Uploaded images for this project
    │
    └── ...
```

---

## Configuration

All configuration is at the top of `app.py`:

| Variable | Default | Description |
|---|---|---|
| `PROJECTS_DIR` | `./projects` | Where project folders are stored |
| `MAX_CONTENT_LENGTH` | 512 MB | Maximum upload size for import |

To change the default template for new projects, edit the `DEFAULT_TEMPLATE` string in `app.py`.
Use `%%PROJECT_NAME%%` as the placeholder — it gets replaced with the project name at creation time.

---

## Troubleshooting

### `pdflatex not found`
TeX Live is not installed or not in your PATH.
```bash
# Verify:
pdflatex --version

# Install (Ubuntu/Debian):
sudo apt install texlive-full lmodern
```

### `File lmodern.sty not found` — compilation fails
The `lmodern` package is missing. Install it separately:
```bash
sudo apt install lmodern
```

### `.rar` import fails
The `unrar-free` package is required for RAR extraction:
```bash
sudo apt install unrar-free
```
On Windows, install WinRAR or 7-Zip and make sure `unrar.exe` is in your PATH.

### Uploaded archive imports but project does not appear on the dashboard
Refresh the page. If the project still does not appear, the archive may not contain
any `.tex` file — make sure your archive includes at least one `.tex` file.

### Compilation succeeds but PDF is blank or incorrect
Run the compilation a second time. Some documents (those with a table of contents,
cross-references, or bibliography) require two passes to resolve all references.
The app already runs `pdflatex` twice automatically, but complex documents may need
a third pass — click **Compile PDF** again.

### Large project uploads fail
Increase `MAX_CONTENT_LENGTH` in `app.py` (default is 512 MB):
```python
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1 GB
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `flask` | Web framework |
| `werkzeug` | WSGI utilities (bundled with Flask) |
| `pdflatex` *(system)* | LaTeX compilation |
| `lmodern` *(system)* | Latin Modern fonts for LaTeX |
| `unrar-free` *(system, optional)* | RAR archive extraction |