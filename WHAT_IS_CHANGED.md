# WinHermes Fork: Differences from Original Hermes Agent

This document summarizes the key differences between the WinHermes fork (`F:\AI\winhermes-agent`) and the original Hermes Agent repository (`https://github.com/NousResearch/hermes-agent`).

## Overview

## 🪟 Major Windows-Specific Features

### 1. Native Windows Support
- Full Windows compatibility without requiring WSL2
- Windows batch script (`setup-hermes.bat`) for automated setup
- Git Bash integration for terminal command execution
- Cross-platform file locking (fcntl on Linux, msvcrt on Windows)

### 2. Windows Code Execution System
**New Files:**
- `tools/ipc_base.py` - Cross-platform IPC abstraction layer
- `tools/ipc_windows.py` - Windows named pipe implementation using pywin32
- `tests/tools/test_windows_ipc.py` - Unit tests for Windows IPC

**Features:**
- Unix domain sockets on Linux/macOS
- Named pipes on Windows (via pywin32)
- TCP localhost fallback for all platforms
- ACL-based security with authentication tokens
- Process isolation with hidden console windows

### 3. Windows Process Management
Modified `tools/environments/local.py`:
- Empty `_SANE_PATH` on Windows (Git Bash manages its own PATH)
- `_temp_prefix` uses `tempfile.gettempdir()` instead of hardcoded `/tmp/`
- `_kill_shell_children()` uses `taskkill /F /T /PID` on Windows
- Proper Windows PATH handling

## 📁 New Files Added

### Documentation
- `ORIGINAL_README.md` - Backup of original README
- `WHAT_IS_CHANGED.md` - This document

### Setup & Scripts
- `setup-hermes.bat` - Windows-native setup script (277 lines)

### Windows IPC System
- `tools/ipc_base.py` - Cross-platform IPC abstraction
- `tools/ipc_windows.py` - Windows named pipe implementation
- `tests/tools/test_windows_ipc.py` - Windows IPC tests

## 🔧 Core File Modifications

### Gateway Enhancements (`gateway/run.py`)
- Agent caching for performance improvement
- Enhanced messaging platform support (SIGNAL, EMAIL, MATTERMOST, MATRIX, DINGTALK)
- Fixed session reset handling with detailed notifications
- Removed problematic token compression multiplier
- Fixed `/model custom` handler and provider switching
- Proper handling of interrupted vs queued messages

### CLI Improvements (`hermes_cli/`)
- `gateway.py`: Added virtual environment detection
- `config.py`: Enhanced configuration system
- `setup.py`: Improved setup wizard
- `models.py`: Updated model catalog

### Tool Modifications
- `tools/memory_tool.py`: Cross-platform file locking
- `tools/process_registry.py`: Windows compatibility fixes
- `tools/code_execution_tool.py`: Major Windows sandbox support
- `tools/environments/local.py`: Windows PATH and process handling
- `tools/environments/persistent_shell.py`: Windows temp directory support
- `tools/browser_tool.py`: Fixed WinError 193 issues

### Agent Core
- `run_agent.py`: Modified agent runner
- `model_tools.py`: Tool orchestration changes
- `agent/context_compressor.py`: Improved context compression
- `agent/insights.py`: Enhanced insights system

## 🚀 Additional Features

### Enhanced Browser Support
- Fixed WinError 193 installation issues
- Full browser automation on Windows
- Both local Chromium and Browserbase cloud support
- Proper PATH and executable detection

### Ollama Integration
- Improved custom provider resolution
- Fixed base URL configuration
- Better model format handling
- Generic endpoint detection for non-OpenRouter URLs

## 🔍 Key Differences Summary

1. **Windows Native Support**: Complete transformation from Linux/WSL-focused to first-class Windows application
2. **Code Execution**: Full sandboxed Python execution on Windows using named pipes or TCP fallback
3. **Setup Automation**: Windows batch script for one-click setup
4. **Process Management**: Windows-specific process handling and security
5. **Gateway Performance**: Agent caching and enhanced platform support
6. **Browser Tools**: Fixed Windows compatibility issues
7. **Ollama Integration**: Improved local model support

## 📝 Notes

- All changes are backward compatible
- Original functionality is preserved
- Windows features use conditional compilation/fallbacks
- Cross-platform compatibility maintained throughout
