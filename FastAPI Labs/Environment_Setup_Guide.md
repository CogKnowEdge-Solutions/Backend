# Environment Setup Guide

This guide gets you from a fresh machine to a running Python notebook, on Windows, macOS, or Linux.

This guide is written for people who aren't yet familiar with IDEs, don't already have Python installed, and are setting up a Python development environment for the first time. It doesn't contain any teaching material of the course itself — it's simply a setup guide for those who don't yet know how to get from a blank machine to a working environment. If you're already comfortable with this kind of setup, feel free to skip it. Pick one of the three setup paths below; you don't need all three.

## Table of Contents

- [1 Before You Start — Prerequisites](#1-before-you-start--prerequisites)
- [2 Installing Python](#2-installing-python)
  - [2.1 Windows](#21-windows)
  - [2.2 macOS](#22-macos)
  - [2.3 Linux](#23-linux)
- [3 Installing JupyterLab](#3-installing-jupyterlab)
- [4 Choose Your Environment](#4-choose-your-environment)
- [5 Option 1: Jupyter Notebook (Local)](#5-option-1-jupyter-notebook-local)
- [6 Option 2: Google Colab](#6-option-2-google-colab)
  - [6.1 Provide Your API Key — The Secure Way](#61-provide-your-api-key--the-secure-way)
  - [6.2 (Alternative) Create an Actual .env File in Colab](#62-alternative-create-an-actual-env-file-in-colab)
- [7 Option 3: VS Code](#7-option-3-vs-code)
- [8 Creating and Configuring Your .env File](#8-creating-and-configuring-your-env-file)
  - [8.1 What It Is and Why It Matters](#81-what-it-is-and-why-it-matters)
  - [8.2 Creating It Manually](#82-creating-it-manually)
  - [8.3 How Your Project Can Verify It Worked](#83-how-your-project-can-verify-it-worked)
  - [8.4 Keeping It Safe](#84-keeping-it-safe)
- [9 Troubleshooting Quick Reference](#9-troubleshooting-quick-reference)

---

## 1 Before You Start — Prerequisites

- **Python 3.10 or newer.** If you're not sure whether you have it, see Section 2, Installing Python.
- **Any API keys or credentials your project needs** (if applicable). Check your project's own documentation for where to get these — many services offer a free tier to get started, so this often costs nothing.
- About 5 minutes and ~300MB of free disk space per project (for its virtual environment).
- **Google Colab needs none of this** — skip straight to Section 6, Option 2, if you'd rather not install anything locally.

## 2 Installing Python

Skip this section if `python3 --version` (macOS/Linux) or `python --version` (Windows) already prints 3.10 or higher.

### 2.1 Windows

1. Download the installer from python.org/downloads (the "Windows installer (64-bit)" link).
2. Run it, and check the box "Add python.exe to PATH" at the bottom of the first screen — this is the step almost everyone misses, and without it none of the commands below will work.
3. Click Install Now.
4. Open a new PowerShell or Command Prompt window and confirm:

```
python --version
```

*Alternative: install from the Microsoft Store (search "Python 3.12") — it handles PATH automatically.*

### 2.2 macOS

The system Python on macOS is old and shouldn't be used for development. Two good options:

- **Homebrew (recommended):** install Homebrew from brew.sh if you don't have it, then run `brew install python@3.12`.
- **Official installer:** download the macOS installer from python.org/downloads and run it.

Confirm with: `python3 --version`

### 2.3 Linux

Most distributions ship a recent-enough Python already. Confirm with `python3 --version`; if it's below 3.10, install a newer one via your package manager, e.g.:

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install python3 python3-venv python3-pip

# Fedora
sudo dnf install python3 python3-pip
```

## 3 Installing JupyterLab

You only need this if you're taking Option 1 (Jupyter Notebook) or Option 3 (VS Code) — Google Colab already has Jupyter running in your browser, nothing to install.

Your project's own pinned `pip install` command (used in the steps below) may already include `jupyterlab`, so it gets installed automatically, fresh, inside your virtual environment — you don't need to install it separately first if so.

To install it manually (for example, to try it out before starting your project, or to have one shared copy you launch notebooks with) — macOS/Linux shown here; on Windows use the create/activate commands from the table in Section 5.2 below, then the same pip install lines:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install jupyterlab
```

To verify it installed correctly: `jupyter --version`

This should print a version table including `jupyterlab`. If instead you get `command not found` / `'jupyter' is not recognized`, your virtual environment likely isn't activated — see the "Command not found" row in Section 9, Troubleshooting.

To launch it on its own (without opening a specific notebook): `jupyter lab`

This opens a file-browser tab in your default browser at `http://localhost:8888`, from which you can navigate to and open any `.ipynb` file.

## 4 Choose Your Environment

If you're not sure, use Jupyter Notebook — it's the simplest default for most projects.

| | Jupyter Notebook | Google Colab | VS Code |
|---|---|---|---|
| **Runs on** | Your own machine | Google's servers (browser only) | Your own machine |
| **Works on** | Windows, macOS, Linux | Any OS with a browser | Windows, macOS, Linux |
| **Install required?** | Yes (Python + packages) | No — just a Google account | Yes (VS Code + extensions) |
| **Best for** | Working fully offline once set up | Quickest start, no local install | Developers who already write code in VS Code day-to-day |
| **.env handling** | Native — a real file in the project folder | Needs an extra step (no persistent disk by default) | Native — a real file in the project folder |
| **Setup time** | ~10 min | ~3 min | ~10 min |

## 5 Option 1: Jupyter Notebook (Local)

**1.** Open a terminal and move into your project folder. If the folder name contains spaces or special characters (e.g. `MyProject(v1)`), quote the name on every platform:

```bash
cd "MyProject(v1)"   # replace with your own project folder — same command on Windows, macOS, and Linux
```

**2.** Create and activate a virtual environment. This keeps your project's packages isolated from everything else on your machine. The create command is the same everywhere; the activate command differs by platform and shell:

```bash
python3 -m venv .venv   # macOS/Linux
python -m venv .venv    # Windows
```

| Platform / Shell | Activate Command |
|---|---|
| macOS / Linux (bash, zsh) | `source .venv/bin/activate` |
| Windows — Command Prompt | `.venv\Scripts\activate.bat` |
| Windows — PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows — Git Bash | `source .venv/Scripts/activate` |

Your terminal prompt should now show `(.venv)` at the start of the line — that confirms the environment is active. (PowerShell note: if you get a "running scripts is disabled" error, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then retry.)

**3.** Install the required packages. Your project's own setup instructions (or its README, or the notebook's first cell) should have the exact `pip install` command, often with versions pinned — copy it from there so you get the versions the project expects:

```bash
pip install --upgrade pip
pip install -qU "package-one==X.Y.Z" "package-two==X.Y.Z" \
  "python-dotenv==X.Y.Z" "jupyterlab" "ipykernel"
```

This command is identical on Windows, macOS, and Linux once your virtual environment is activated.

**4.** Set up your `.env` file. See Section 8 below for full detail — in short:

```bash
cp .env.example .env          # macOS/Linux/Git Bash
copy .env.example .env        # Windows Command Prompt
Copy-Item .env.example .env   # Windows PowerShell
```

Then open `.env` in any text editor and paste your real credentials in place of the placeholders.

**5.** Launch Jupyter and open the notebook:

```bash
jupyter lab your-notebook.ipynb   # replace with your project's .ipynb filename — same on every platform
```

This opens a browser tab. Run each cell top to bottom with Shift+Enter. Don't skip ahead — later cells often depend on variables created earlier.

**6.** When you're done, deactivate the environment (optional, but tidy) — same command everywhere:

```bash
deactivate
```

## 6 Option 2: Google Colab

Colab runs entirely in your browser on Google's servers, so there's nothing to install locally, and it works identically on Windows, macOS, Linux, or even a Chromebook — but it has no persistent disk by default, which changes how you handle packages and any credentials.

**1.** Upload the notebook. Go to colab.research.google.com → File → Upload notebook, and select your project's `.ipynb` file from your computer.

**2.** Install packages in a cell. Colab comes with many packages preinstalled but likely not your project's specific pinned versions. Add a new cell at the top with an `!` prefix (Colab's syntax for running a shell command) and run it first:

```bash
!pip install -qU "package-one==X.Y.Z" "package-two==X.Y.Z" \
  "python-dotenv==X.Y.Z"
```

Use the exact versions from your project's own setup instructions, same as the local path.

### 6.1 Provide Your API Key — The Secure Way

Do not paste any real credentials directly into a code cell; if you ever share or publish that notebook, they go with it. Colab has a built-in secrets manager instead:

- Click the key icon (🔑) in the left sidebar.
- Click **Add new secret**, give it a name (e.g. `API_KEY`), and paste your real value as the value.
- Toggle **Notebook access** on for this notebook.

In a code cell, read it like this:

```python
from google.colab import userdata
import os
os.environ["API_KEY"] = userdata.get("API_KEY")
```

This achieves the same thing `load_dotenv()` does locally — it puts the value into `os.environ` before your code reads it — without the credential ever appearing in the notebook's own text.

### 6.2 (Alternative) Create an Actual .env File in Colab

If you'd rather match the local setup exactly, you can write a real `.env` file into Colab's temporary filesystem:

```
%%writefile .env
API_KEY=your-real-value-here
```

Run that cell once, then `load_dotenv()` works exactly as it does locally. The catch: Colab's filesystem is wiped when the runtime disconnects (closing the tab, an idle timeout, or a manual "Disconnect and delete runtime"), so you'd need to re-run that cell at the start of every new session. The Secrets approach above persists across sessions tied to your Google account, so it's the better default for Colab.

**5.** Run the rest of the notebook top to bottom with Shift+Enter, same as local Jupyter.

## 7 Option 3: VS Code

VS Code itself is identical across Windows, macOS, and Linux — the only platform differences are the same venv-activation and .env-creation commands used in Section 5, shown again below.

**1.** Install two extensions (Extensions panel — Ctrl+Shift+X on Windows/Linux, Cmd+Shift+X on macOS): **Python** and **Jupyter**, both published by Microsoft.

**2.** Open your project folder. File → Open Folder… and select the specific project folder (e.g. `MyProject(v1)`), not a parent folder containing multiple projects — this keeps VS Code's Python interpreter picker scoped correctly.

**3.** Create a virtual environment. Open the built-in terminal (Ctrl+`) and run the same create/activate commands as Section 5.2 — VS Code's integrated terminal defaults to PowerShell on Windows and bash/zsh on macOS/Linux, so use the matching row from that table.

Alternatively, use the Command Palette (Ctrl+Shift+P / Cmd+Shift+P) → "Python: Create Environment" → Venv, and let VS Code do it for you — this works identically on all three platforms and sidesteps the activation-command differences entirely.

**4.** Install the required packages the same way as Section 5, step 3 — either in the terminal or in the notebook's own first cell.

**5.** Select the interpreter. Command Palette → "Python: Select Interpreter" → choose the `.venv` you just created (shows as `./.venv/bin/python` on macOS/Linux or `.\.venv\Scripts\python.exe` on Windows). This is the step people miss most often — if VS Code runs cells with the wrong interpreter, your imports will fail even though you installed the packages.

**6.** Set up your `.env` file the same way as Section 5, step 4. VS Code has a New File button in the Explorer panel if you'd rather create `.env` by hand than copy `.env.example` — this works the same on every platform, and avoids the OS-specific copy commands entirely.

**7.** Open the `.ipynb` file directly in VS Code — it renders and runs notebooks natively. Click the kernel picker in the top right and confirm it's using your project's `.venv`, then run cells with Shift+Enter.

## 8 Creating and Configuring Your .env File

### 8.1 What It Is and Why It Matters

A `.env` file is a small plain-text file that holds secrets — API keys, tokens, passwords — outside your actual code. Many Python projects call `load_dotenv()` (from the `python-dotenv` package) at the start, which reads this file and loads its contents into `os.environ`, the same place environment variables normally live. Your code then reads a value with `os.getenv("SOME_KEY")` instead of having it typed directly into a cell.

This matters for one reason: code gets shared, screen-shared, and committed to git — secrets shouldn't be. If a credential is typed directly into a notebook cell and you ever push that notebook to GitHub or paste it into a chat, it leaks with it. A `.env` file, kept out of git, doesn't have that problem. This is not platform-specific — the risk and the fix are the same on Windows, macOS, and Linux.

### 8.2 Creating It Manually

Many project folders already contain a `.env.example` — a template with fake placeholder values. The fastest path is copying it (pick the command for your platform, shown in Section 5, step 4).

If you'd rather create it from scratch, the file just needs to exist at the root of your project folder (next to the `.ipynb` file) and contain one line per value, e.g.:

```
API_KEY=your-real-value-here
```

Ways to create that file by hand, on every platform:

| Where | How |
|---|---|
| macOS/Linux terminal | `nano .env` (or `vim .env`), type the line, save and exit |
| Windows — PowerShell | `New-Item .env` then open it in Notepad: `notepad .env` |
| Windows — Command Prompt | `type nul > .env` then open it in Notepad: `notepad .env` |
| Windows — Notepad directly | File → Save As → filename `.env`, and change "Save as type" to All Files (otherwise Notepad silently appends `.txt`) |
| VS Code (any platform) | Explorer panel → New File → name it `.env` → type the line → save |
| Google Colab | `%%writefile .env` in a cell (see Section 6.2) |

A few details that trip people up, on any platform:

- No quotes needed around the value: `API_KEY=abc123`, not `API_KEY="abc123"`. Quotes usually still work with python-dotenv, but leaving them off avoids edge cases.
- No spaces around the `=` — `KEY=value`, not `KEY = value`.
- The filename is exactly `.env` — a leading dot, no extension. This trips up Windows users most often, since some editors (Notepad especially) try to save it as `.env.txt` by default; check the actual filename in File Explorer (with "File name extensions" turned on in the View tab) or `dir /a` afterward.
- Location matters. `load_dotenv()` looks in the current working directory by default. If you launch Jupyter or run your script from anywhere other than your project folder itself, it won't find the file. Always `cd` into the specific project folder first, on any platform.

### 8.3 How Your Project Can Verify It Worked

Many projects include a small guard cell, right after `load_dotenv()`, along these lines:

```python
if not os.getenv("API_KEY"):
    raise SystemExit("No API_KEY found. Add it to .env and restart the kernel.")
```

If this raises, the three most common causes are: the `.env` file doesn't exist yet (you skipped the copy/create step), it exists but is in the wrong folder (see "Location matters" in 8.2), or you edited it after starting Jupyter — environment variables are loaded once, at cell-run time, so save the file and re-run the `load_dotenv()` cell (or restart the kernel) after any change. None of this differs by platform.

### 8.4 Keeping It Safe

- **Never commit `.env` to git.** Most project templates already exclude it via `.gitignore`, so a plain `git add .` won't pick it up — but double-check with `git status` before pushing if you're ever unsure.
- **Never paste your real credentials** into a notebook cell, a chat, or a screenshot. Use `.env` (or Colab Secrets) every time, even for quick tests.
- If a credential ever leaks (committed by accident, pasted somewhere public), revoke it immediately with the provider and generate a new one — revoking is usually instant and free.

## 9 Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named '...'` | Wrong Python interpreter, or venv not activated | Confirm `(.venv)` shows in your terminal prompt, or re-select the interpreter in VS Code |
| `'python' is not recognized` / `'jupyter' is not recognized` (Windows) | Python wasn't added to PATH during install | Re-run the Python installer and check "Add python.exe to PATH", or reinstall via the Microsoft Store |
| `command not found: python3` (macOS/Linux) | Python not installed, or only `python` exists, not `python3` | See Section 2, Installing Python; try `python --version` as a fallback |
| `SystemExit: No API_KEY found` (or similar) | `.env` missing, misnamed, or in the wrong folder | Re-check filename is exactly `.env` (not `.env.txt`), and that it sits next to the notebook you're running |
| Credentials load locally but not in Colab | Colab has no persistent disk | Use Colab Secrets (Section 6.1), or re-run the `%%writefile .env` cell this session |
| `pip install` fails or hangs | No internet, or a version pin no longer available | Retry with `-v` for verbose output; confirm you copied the pinned versions from your project's own setup instructions |
| PowerShell: "running scripts is disabled on this system" | Default PowerShell execution policy blocks venv activation | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then retry `.venv\Scripts\Activate.ps1` |
| Notebook runs but gives unexpected API errors | A free-tier or rate-limited service you depend on is temporarily unavailable | Check the provider's status page; consider swapping to another available option if needed |
