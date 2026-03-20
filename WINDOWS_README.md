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
- `tools/code_execution_tool.py` — **NOW ENABLED ON WINDOWS** - Full sandboxed Python execution with cross-platform IPC
- Uses named pipes on Windows (pywin32) with security ACLs
- Falls back to TCP localhost if pywin32 not available
- Unix domain sockets on Linux/macOS, TCP fallback everywhere
- Windows process creation with hidden console windows
- Cross-platform endpoint generation and environment passing
- `hermes_cli/auth.py` — `fcntl`/`msvcrt` fallback
- `cron/scheduler.py` — `fcntl`/`msvcrt` fallback
- `pyproject.toml` — `pywinpty` for Windows PTY support

### New Windows-Specific Files
- `tools/ipc_base.py` — Cross-platform IPC abstraction layer
- `tools/ipc_windows.py` — Windows named pipe implementation using pywin32
- `tests/tools/test_windows_ipc.py` — Unit tests for all IPC transports

### Code Execution Implementation
The Windows code execution implementation includes:

1. **Cross-Platform IPC Abstraction** (`tools/ipc_base.py`)
   - Base class for all IPC transports
   - Unix domain sockets for Linux/macOS
   - Windows named pipes (via pywin32)
   - TCP localhost fallback for all platforms
   - Automatic transport selection based on platform

2. **Windows Named Pipes** (`tools/ipc_windows.py`)
   - Secure named pipe server/client using pywin32
   - ACL-based security (current user only)
   - Authentication tokens for sandbox isolation
   - Graceful fallback when pywin32 unavailable

3. **Updated Code Execution Tool**
   - Uses IPC abstraction instead of hardcoded UDS
   - Cross-platform endpoint generation
   - Windows-specific process creation (hidden console)
   - Proper environment variable passing for IPC type
   - Maintains same security model as original

## Windows-Specific Features

- **Native Windows support** - No WSL2 required
- **Code execution on Windows** - Full sandboxed Python execution with named pipes or TCP fallback
- **Cross-platform IPC abstraction** - Unix domain sockets (Linux/macOS), named pipes (Windows), TCP fallback
- **Windows process sandboxing** - Proper process isolation with hidden console windows
- **Ollama integration** - Fixed provider resolution for local models
- **Custom endpoint support** - Enhanced detection for OpenAI-compatible APIs
- **Windows path handling** - Proper handling of Windows file paths
- **PowerShell scripts** - Windows-native automation scripts

## Ollama Integration on Windows

WinHermes includes improved Ollama support for Windows users:

```yaml
# ~/.hermes/config.yaml
model:
  default: qwen3.5:4b
  provider: custom
  base_url: http://localhost:11434/v1
```

```batch
# Run with Ollama
hermes --model qwen3.5:4b --base-url http://localhost:11434/v1
```

**Fixed Issues:**
- **Custom provider resolution now correctly returns `provider: "openai"` for OpenAI-compatible endpoints**
- **Generic endpoint detection properly identifies non-OpenRouter URLs**
- **Base URL configuration added for custom providers**
- **Model format fixed for LiteLLM compatibility (no `ollama/` prefix needed)**

**Note:** Some models (like qwen3.5:4b) don't support function calling. Use tool-compatible models like Llama 3.1 for full tool support.

## Recent Windows Updates

- **Added Windows code execution support** - Full sandboxed Python execution with cross-platform IPC abstraction
- **Implemented Windows named pipes** - Secure IPC transport using pywin32 with ACLs and authentication
- **Cross-platform IPC abstraction** - Unix domain sockets (Linux/macOS), named pipes (Windows), TCP fallback
- **Windows process sandboxing** - Proper process isolation with hidden console windows and security
- **Fixed custom provider resolution** - Custom endpoints now correctly return `provider: "openai"` instead of hardcoded `"openrouter"`
- **Enhanced endpoint detection** - Generic fallback now detects endpoint type based on URL
- **Ollama integration** - Full support for local Ollama models with proper configuration
- **Windows path handling** - Improved file path handling for Windows environments
- **Telegram gateway fixes** - Resolved media path errors on Windows

## Configuration Examples

### Custom Provider (Ollama) Configuration
```yaml
# ~/.hermes/config.yaml
model:
  default: llama3.1:8b
  provider: custom
  base_url: http://localhost:11434/v1

# Environment variables (.env)
OPENAI_API_KEY=dummy-key
OPENAI_BASE_URL=http://localhost:11434/v1
```

### Direct Command Line Usage
```batch
# Using Ollama with a tool-compatible model
hermes --model llama3.1:8b --base-url http://localhost:11434/v1

# Using OpenRouter
hermes --model openrouter:meta-llama/llama-3.1-8b-instruct

# Using custom endpoint
hermes --model custom:gpt-4o --base-url https://api.example.com/v1
```

## Known Limitations on Windows

1. **Code Execution Tool** — **NOW ENABLED**. Requires `pywin32` for named pipe support (falls back to TCP if not installed).
2. **Docker/Modal/Singularity environments** — Work but require their respective Windows installations.
3. **PTY mode** — Uses `pywinpty` (automatically installed). Some interactive CLI tools may behave differently.
4. **File paths** — Hermes uses forward slashes internally (bash-compatible). Windows backslash paths work for Python file operations.
5. **Some models** (e.g., qwen3.5:4b in Ollama) don't support function calling through OpenAI API format.
6. **Telegram gateway** may show media path errors for invalid MEDIA: tags (cosmetic issue).
7. **Model-specific parameters** (like thinking mode) may not be exposed through all providers.

## Environment Variables

- `HERMES_HOME` — Override config directory (default: `%USERPROFILE%\.hermes`)
- `HERMES_GIT_BASH_PATH` — Override Git Bash location if auto-detection fails
- The setup batch file sets `HERMES_GIT_BASH_PATH` in the launcher script

## Troubleshooting

**"Git Bash not found"**
→ Install Git for Windows, or set `HERMES_GIT_BASH_PATH` to your `bash.exe` path

**"hermes is not recognized"**
→ Add `%USERPROFILE%\.local\bin` to your PATH, or use the full path:
  `F:\AI\winhermes-agent\venv\Scripts\hermes.exe`

**"Terminal commands fail with path errors"**
→ Ensure Git for Windows is installed and `bash.exe` is accessible

**"Permission errors on .hermes directory"**
→ Run `hermes setup` once to create the directory structure with correct permissions

**Fork guide**
```bash
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git pull upstream main
```

## Success Story: Code Execution on Windows

**Successfully enabled qwen3.5:9b with tool calling!**

After implementing Windows code execution support with cross-platform IPC abstraction:

- qwen3.5:9b model can now successfully call tools like `terminal()`, `read_file()`, `write_file()`
- Agent can execute multi-step Python scripts in a sandboxed environment
- Uses Windows named pipes (with pywin32) for secure IPC
- Falls back to TCP localhost if pywin32 is not available

**Configuration that works:**
```yaml
model:
  default: qwen3.5:9b
  provider: custom
  base_url: http://localhost:11434/v1
```

**Example successful tool call:**
```python
# Agent can now run this in execute_code:
result = terminal("ls -la")
print(f"Found {len(result.split())} files")