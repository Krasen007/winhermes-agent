# Hermes Agent - Windows Native Setup

This is a Windows-native port of the Hermes Agent, located at `F:\AI\hermes-agent`.

## Prerequisites

1. **Git for Windows** (required)
   - Download: https://git-scm.com/download/win
   - Provides `bash.exe` which Hermes uses for terminal command execution
   - Default install location works fine

2. **Python 3.11+** (uv can install this automatically)
   - Or install from https://www.python.org/downloads/

## Quick Setup

```batch
cd F:\AI\hermes-agent
setup-hermes.bat
```

The script will:
- Install `uv` (fast Python package manager)
- Create a virtual environment
- Install all dependencies
- Create a `hermes.cmd` launcher
- Seed bundled skills

## Running Hermes

After setup, open a **new terminal** and run:

```batch
hermes
```

Or if `hermes` isn't on PATH yet:

```batch
F:\AI\hermes-agent\venv\Scripts\hermes.exe
```

## Configuration

API keys go in `%USERPROFILE%\.hermes\.env` (e.g., `C:\Users\Krasen\.hermes\.env`)

Run the setup wizard to configure:
```batch
hermes setup
```

## What Changed from Linux Version

The following files were modified for Windows compatibility:

### `tools/memory_tool.py`
- `import fcntl` → cross-platform: `fcntl` on Linux, `msvcrt` on Windows
- File locking uses `msvcrt.locking()` on Windows instead of `fcntl.flock()`

### `tools/environments/local.py`
- `_SANE_PATH` is empty on Windows (Git Bash manages its own PATH)
- `_make_run_env()` skips PATH modification on Windows
- `_temp_prefix` uses `tempfile.gettempdir()` instead of hardcoded `/tmp/`
- `_kill_shell_children()` uses `taskkill /F /T /PID` on Windows instead of `pkill -P`
- `_find_bash()` already had Windows support (finds Git Bash)

### `tools/environments/persistent_shell.py`
- `_temp_prefix` uses `tempfile.gettempdir()` instead of hardcoded `/tmp/`

### Already Had Windows Support
These files already contained Windows compatibility code:
- `tools/terminal_tool.py` — `msvcrt` for password input
- `tools/process_registry.py` — `_IS_WINDOWS` flag, guarded `preexec_fn`
- `tools/code_execution_tool.py` — disabled on Windows (UDS not available)
- `hermes_cli/auth.py` — `fcntl`/`msvcrt` fallback
- `cron/scheduler.py` — `fcntl`/`msvcrt` fallback
- `pyproject.toml` — `pywinpty` for Windows PTY support

## Known Limitations on Windows

1. **Code Execution Tool** — Disabled. Uses Unix domain sockets which aren't available on Windows.
2. **Docker/Modal/Singularity environments** — Work but require their respective Windows installations.
3. **PTY mode** — Uses `pywinpty` (automatically installed). Some interactive CLI tools may behave differently.
4. **File paths** — Hermes uses forward slashes internally (bash-compatible). Windows backslash paths work for Python file operations.

## Environment Variables

- `HERMES_HOME` — Override the config directory (default: `%USERPROFILE%\.hermes`)
- `HERMES_GIT_BASH_PATH` — Override Git Bash location if auto-detection fails
- The setup batch file sets `HERMES_GIT_BASH_PATH` in the launcher script

## Troubleshooting

**"Git Bash not found"**
→ Install Git for Windows, or set `HERMES_GIT_BASH_PATH` to your `bash.exe` path

**"hermes is not recognized"**
→ Add `%USERPROFILE%\.local\bin` to your PATH, or use the full path:
  `F:\AI\hermes-agent\venv\Scripts\hermes.exe`

**Terminal commands fail with path errors**
→ Ensure Git for Windows is installed and `bash.exe` is accessible

**Permission errors on .hermes directory**
→ Run `hermes setup` once to create the directory structure with correct permissions
