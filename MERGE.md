# Merge Summary: Hermes Agent Major Feature Update

This merge brings significant new features and improvements to Hermes Agent, including context references, plugin system, CLI extensions, enhanced Windows support, and more.

## 🆕 Major New Features

### 1. Context References (`@file:`, `@folder:`, `@diff`, etc.)
**File**: `agent/context_references.py`

Automatically expand contextual references in messages to inject file contents, folder listings, git diffs, and more.

**Usage Examples**:
- `@file:README.md` - Inject file contents
- `@folder:src` - Show folder structure
- `@diff` - Show git diff of staged changes
- `@staged` - Show staged files
- `@url:https://example.com` - Extract web content

**Key Benefits**:
- Works in CLI, gateway, and ACP adapter
- Automatic token counting and limits
- Cross-platform path handling
- Async processing for web content

### 2. Plugin System
**Files**: `hermes_cli/plugins_cmd.py`, plugin infrastructure

Install, manage, and use external plugins that add tools, hooks, and skills to Hermes.

**Commands**:
```bash
hermes plugins list                    # List installed plugins
hermes plugins install owner/repo      # Install from GitHub
hermes plugins install https://url      # Install from any Git repo
hermes plugins remove calculator        # Remove a plugin
hermes plugins update calculator        # Update to latest version
```

**Plugin Structure**:
```
~/.hermes/plugins/calculator/
├── plugin.yaml          # Manifest
├── schemas.py           # Tool schemas
├── tools.py             # Tool implementations
├── hooks.py             # Optional lifecycle hooks
└── skill/               # Optional bundled skills
```

### 3. CLI Extension System
**File**: `website/docs/developer-guide/extending-the-cli.md`

Protected hooks for building wrapper CLIs that extend Hermes TUI without overriding internals.

**Extension Points**:
- `_get_extra_tui_widgets()` - Add UI panels
- `_register_extra_tui_keybindings()` - Add hotkeys
- `_build_tui_layout_children()` - Control layout
- `process_command()` - Add slash commands
- `_build_tui_style_dict()` - Custom styling

**Example**:
```python
class MyCLI(HermesCLI):
    def _get_extra_tui_widgets(self):
        return [Window(FormattedTextControl("Custom panel"))]
```

### 4. Enhanced Windows Support
**File**: `tools/code_execution_tool.py`

Full sandboxed Python code execution now works on Windows using named pipes or TCP fallback.

**Features**:
- Cross-platform IPC abstraction
- Named pipes on Windows (via pywin32)
- TCP fallback when pipes unavailable
- Process isolation and security
- All 7 sandbox tools work on Windows

### 5. Agent Caching in Gateway
**File**: `gateway/run.py`

Gateway now caches AIAgent instances per session to preserve prompt cache hits and reduce startup overhead.

**Benefits**:
- Significant performance improvement
- Preserves frozen system prompts
- Maintains tool schemas for cache hits
- Automatic cache invalidation on config change

## 🔄 Improvements & Enhancements

### Agent Core
- **Anthropic Adapter**: Added `preserve_dots` parameter for better Claude support
- **Context Compression**: Improved memory usage and session splitting
- **Auxiliary Client**: Base URL override support from config
- **Prompt Caching**: Enhanced cache control and invalidation
- **Model Metadata**: Better context length detection and token estimation

### Tools & Skills
- **Code Execution**: Full Windows compatibility with IPC abstraction
- **Session Search**: Enhanced search capabilities in conversations
- **Terminal Tool**: Improved Windows PTY support via pywinpty
- **New Skills**:
  - `meme-generation`: Generate real meme images with Pillow
  - `bioinformatics`: Bioinformatics tools and workflows

### CLI & User Experience
- **Plugin Management**: Full CLI for installing/removing plugins
- **Skin Engine**: Data-driven CLI theming system
- **Banner**: Improved startup display with skin support
- **Setup Wizard**: Enhanced interactive configuration
- **Auth**: Better credential management across providers

### Gateway & Messaging
- **Agent Cache**: Per-session agent caching for performance
- **Context References**: Automatic expansion in all platforms
- **Platform Adapters**: Enhanced Mattermost, Signal, WhatsApp support
- **Status**: Better process detection on Unix systems
- **Error Handling**: Improved fallback and retry logic

### Testing & Documentation
- **New Tests**: Comprehensive coverage for new features
- **Plugin Guide**: Step-by-step plugin development tutorial
- **CLI Extension Guide**: How to build wrapper CLIs
- **Environment Variables**: Complete reference documentation

## 🛠️ How to Use New Features

### Context References
Simply use `@` syntax in any message:
```
Summarize @file:README.md and list @folder:src contents
```

### Plugin System
```bash
# Install a plugin
hermes plugins install hermes-ai/calculator-plugin

# List installed plugins
hermes plugins list

# Use plugin tools immediately (no restart needed)
```

### CLI Extensions
Create a wrapper script:
```python
from cli import HermesCLI

class MyCLI(HermesCLI):
    def _get_extra_tui_widgets(self):
        # Add custom UI elements
        pass

if __name__ == "__main__":
    MyCLI().run()
```

### Windows Code Execution
Works out of the box on Windows with Python 3.8+:
- Uses named pipes by default
- Falls back to TCP if pywin32 unavailable
- Full sandbox isolation maintained

## 📦 Dependencies

### New Optional Dependencies
- `pywin32` - Windows named pipe support (auto-installed on Windows)
- `pywinpty` - Windows PTY support for terminal tool

### Updated Dependencies
- `prompt_toolkit` - For enhanced CLI widgets
- Various security and compatibility updates

## 🔧 Configuration

### New Config Options
```yaml
display:
  skin: "default"  # CLI theme

model:
  base_url: "https://api.anthropic.com"  # Can override for auxiliary client

plugins:
  auto_update: true  # Auto-update plugins
```

### Environment Variables
- `HERMES_IPC_TRANSPORT` - Force IPC transport type
- `HERMES_IPC_ENDPOINT` - IPC endpoint for code execution

## 🐛 Bug Fixes

- Fixed memory flush API call failures
- Resolved agent caching issues in gateway
- Fixed Windows path handling in various tools
- Corrected indentation and syntax errors from merge
- Improved error handling in auxiliary client

## 🔄 Migration Notes

### For Users
- No breaking changes
- All existing scripts continue to work
- New features are opt-in

### For Plugin Developers
- New plugin manifest version (1.0)
- Enhanced tool schema validation
- Better error messages for invalid plugins

### For CLI Extenders
- Protected hooks now available
- No need to override internal methods
- Cleaner separation of concerns

## 📚 Documentation

- [Plugin Development Guide](website/docs/guides/build-a-hermes-plugin.md)
- [CLI Extension Guide](website/docs/developer-guide/extending-the-cli.md)
- [Context References](website/docs/user-guide/features/context-references.md)
- [Windows Support](WINDOWS_README.md)

## 🎉 Summary

This is one of the largest feature updates in Hermes Agent history, bringing:
- ✅ Context-aware file/folder/diff references
- ✅ Full plugin ecosystem
- ✅ CLI extension system
- ✅ Complete Windows code execution
- ✅ Major performance improvements
- ✅ Enhanced user experience

All changes are backward compatible and preserve existing functionality while adding powerful new capabilities for both users and developers.
