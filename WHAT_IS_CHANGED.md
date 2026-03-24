# WinHermes Fork: Differences from Original Hermes Agent

This document summarizes the key differences between the WinHermes fork (`F:\AI\winhermes-agent`) and the original Hermes Agent repository (`https://github.com/NousResearch/hermes-agent`).

## Overview

- **Total changed files**: 242
- **Core modified files**: 35 (excluding mini-swe-agent submodule, tests, and docs)
- **Commits ahead**: 20
- **Primary focus**: Native Windows support and enhanced functionality

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
- `MERGE.md` - This document
- `plan.md` - Development planning document

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

### Mini-SWE Agent Integration
Complete mini-swe-agent submodule added with:
- Extensive test suite (~3000+ tests)
- Multiple environment backends (Docker, Singularity, Modal)
- Model integrations (Anthropic, OpenRouter, Portkey, etc.)

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

## 📊 Statistics

### File Changes Breakdown
- **Core modified files**: 35
- **Mini-swe-agent files**: 190
- **Test files**: 17
- **Website documentation**: 0 (excluded from this analysis)

### Commit History
Key commits include:
- `97bb0e6a` - update readme
- `aeb55046` - merge to 0.4.0
- `4f7931eb` - Fix merge conflicts for Windows port
- `c85d6b1c` - feat: Add Windows code execution support
- `89a34c93` - basic working version for windows including ollama support

## 🔍 Key Differences Summary

1. **Windows Native Support**: Complete transformation from Linux/WSL-focused to first-class Windows application
2. **Code Execution**: Full sandboxed Python execution on Windows using named pipes or TCP fallback
3. **Setup Automation**: Windows batch script for one-click setup
4. **Process Management**: Windows-specific process handling and security
5. **Gateway Performance**: Agent caching and enhanced platform support
6. **Browser Tools**: Fixed Windows compatibility issues
7. **Ollama Integration**: Improved local model support

## � Sync Status

Your fork is actively maintained but behind upstream by several commits. Consider merging upstream changes to get the latest bug fixes and features while preserving Windows functionality.

## 📝 Notes

- All changes are backward compatible
- Original functionality is preserved
- Windows features use conditional compilation/fallbacks
- Cross-platform compatibility maintained throughout
