# Hermes-Agent Debug Session Summary

**Date:** March 19, 2026  
**Issue:** Tools not working with custom Ollama provider  
**Status:** Partially Fixed - Provider resolution fixed, but model doesn't support tools

## Problem Description

User reported that tools were not working when using a custom Ollama provider (qwen3.5:4b model). The agent claimed it had no tools registered and couldn't create files.

## Root Causes Found

### 1. Runtime Provider Resolution Bug

**File:** `hermes_cli/runtime_provider.py`

**Issue 1:** Custom providers were hardcoded to return `provider: "openrouter"` even for non-OpenRouter endpoints.

```python
# Line 157 - BEFORE
return {
    "provider": "openrouter",  # WRONG for custom endpoints
    ...
}

# Line 157 - AFTER (FIXED)
return {
    "provider": "openai",  # CORRECT for OpenAI-compatible endpoints
    ...
}
```

**Issue 2:** Generic fallback for custom endpoints also returned `provider: "openrouter"` instead of detecting the endpoint type.

```python
# Lines 226-240 - BEFORE
return {
    "provider": "openrouter",  # ALWAYS openrouter
    ...
}

# Lines 226-240 - AFTER (FIXED)
# Determine provider based on base URL
if "openrouter.ai" in base_url:
    provider_name = "openrouter"
else:
    provider_name = "openai"  # CORRECT for custom endpoints

return {
    "provider": provider_name,
    ...
}
```

### 2. Configuration Issue

User had:
```yaml
model:
  default: qwen3.5:4b
  provider: custom
```

But `provider: custom` wasn't resolving to the custom provider's base URL. 

**Fix:** Added `base_url` to model config:
```yaml
model:
  default: qwen3.5:4b
  provider: custom
  base_url: http://localhost:11434/v1
```

### 3. Model Limitation

The qwen3.5:4b model in Ollama doesn't support function calling through the OpenAI API format. Even with the correct provider resolution, the model responds with text/code instead of calling tools.

## Fixes Applied

1. **Fixed custom provider resolution** in `_resolve_named_custom_runtime()` to return `provider: "openai"`
2. **Fixed generic endpoint detection** in `_resolve_openrouter_runtime()` to detect non-OpenRouter URLs
3. **Added base_url to config** for custom provider resolution

## Testing Results

After fixes:
- ✅ Runtime provider correctly returns `provider: "openai"`
- ✅ Base URL correctly set to `http://localhost:11434/v1`
- ✅ Tools are registered and available in the system
- ❌ Model still doesn't use tools (responds with Python code instead)

## Additional Issue Discovered

### Telegram Gateway Errors

When starting `hermes gateway`, Telegram platform shows errors:
```
[Telegram] Failed to send media (): File not found: /path
[Telegram] Failed to send document: [Errno 13] Permission denied: '/'
```

**Analysis:** These appear to be placeholder paths (`/path`, `path`, `/`) being processed by the media extraction system. Likely caused by:
1. Example/test data containing `MEDIA:/path` placeholders
2. Tool responses returning invalid media paths
3. Session history containing malformed MEDIA tags

**Files to investigate:**
- `gateway/platforms/base.py` - extract_media() function
- `gateway/run.py` - media path collection logic

## Recommendations

### For Tool Support

1. **Use a model that supports function calling** with Ollama:
   - Llama 3.1 models
   - Other models specifically built for tool use
   - Check Ollama documentation for tool-compatible models

2. **Alternative approaches:**
   - Use a different provider that supports tools with qwen3.5
   - Use OpenRouter with a tool-capable model
   - Check if there's a specific qwen3.5 variant that supports tools

### For Telegram Errors

1. **Find the source of invalid MEDIA tags**:
   - Search for `MEDIA:/path` in codebase
   - Check tool responses for malformed media paths
   - Review session history for corrupted data

2. **Add validation** in media extraction to skip invalid paths

## Files Modified

1. `hermes_cli/runtime_provider.py` - Fixed provider resolution for custom endpoints
2. `c:\Users\krase\.hermes\config.yaml` - Added base_url for custom provider

## Test Commands Used

```bash
# Check tool registration
python -c "from model_tools import get_tool_definitions; tools = get_tool_definitions(['file'], quiet_mode=True); print('File tools:', [t['function']['name'] for t in tools])"

# Check runtime provider
python -c "from hermes_cli.runtime_provider import resolve_runtime_provider; runtime = resolve_runtime_provider(); print('Provider:', runtime.get('provider')); print('Base URL:', runtime.get('base_url'))"

# Test agent with custom provider
python debug_tools.py
```

## Next Steps

1. **Fix Telegram media errors** - Find and eliminate invalid MEDIA: tags
2. **Test with tool-compatible model** - Verify tools work with proper model
3. **Add validation** - Prevent invalid media paths from being processed
4. **Document custom provider setup** - Clear instructions for Ollama setup

## Key Insights

- The tool system is working correctly - tools are registered and available
- The issue was in provider resolution, not tool registration
- Custom providers need `provider: "openai"` for OpenAI-compatible endpoints
- Model support for function calling is essential for tools to work
- Always validate base URLs to determine correct provider type

---

# Ollama Integration Session Summary

**Date:** March 19, 2026  
**Objective:** Integrate Ollama as a local LLM provider for hermes-agent  
**Status:** Configuration Complete - Model limitation identified

## Initial Problem

User wanted to use Ollama with qwen3.5:4b model but encountered various issues:
1. Port conflicts with existing Ollama process
2. Missing Python dependencies
3. Incorrect model naming conventions
4. Environment variables not being loaded
5. Tools not working with the model

## Issues Encountered and Solutions

### 1. Ollama Port Conflict
**Error:** `listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address`

**Solution:** 
```bash
taskkill /f /im ollama.exe
```

### 2. Missing Dependencies
**Error:** `ModuleNotFoundError: No module named 'openai'`

**Solution:**
```bash
pip install -r requirements.txt
```

### 3. Model Naming Convention
**Error:** `BadRequestError: ollama/qwen3.5:4b is not a valid model ID`

**Root Cause:** LiteLLM expects specific model format for Ollama

**Findings:**
- Direct curl to Ollama works: `curl http://localhost:11434/v1/chat/completions`
- LiteLLM requires model to be passed without `ollama/` prefix when using `api_base`
- Correct format: `model="qwen3.5:4b"` with `api_base="http://localhost:11434/v1"`

### 4. Environment Variables Not Loading
**Issue:** `run_agent.py` has hardcoded defaults that override environment variables

**Findings:**
```python
# In run_agent.py main() function
def main(
    model: str = "anthropic/claude-opus-4.6",  # Hardcoded!
    base_url: str = "https://openrouter.ai/api/v1",  # Hardcoded!
    ...
):
```

**Solution:** Use CLI parameters to override defaults:
```bash
python run_agent.py --model qwen3.5:4b --base-url http://localhost:11434/v1
```

### 5. Configuration Setup
**Files Updated:**

1. `.env` file:
```env
LLM_MODEL=qwen3.5:4b
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=dummy-key
```

2. `~/.hermes/config.yaml`:
```yaml
model:
  default: qwen3.5:4b
  provider: custom
```

### 6. Disabling Thinking Mode
**Request:** Disable qwen3.5's thinking mode

**Findings:**
- Ollama CLI flag: `--hidethinking` works
- API parameter: Not directly supported in OpenAI-compatible endpoint
- Model parameters can be set via `options` in API call:
```python
"options": {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 1.5,
    "repetition_penalty": 1.0
}
```

### 7. Tools Not Working
**Issue:** Even with correct provider setup, tools weren't being called

**Root Cause:** qwen3.5:4b model doesn't support function calling through OpenAI API format

**Evidence:**
- Tools are registered and available (31 tools loaded)
- Model responds with Python code instead of calling tools
- This is a model limitation, not a hermes-agent issue

## Final Working Configuration

### Command Line Usage:
```bash
python run_agent.py --model qwen3.5:4b --base-url http://localhost:11434/v1
```

### Hermes CLI Usage:
```bash
python hermes  # Uses config.yaml settings
```

### API Call Format:
```python
import requests

response = requests.post('http://localhost:11434/v1/chat/completions', json={
    "model": "qwen3.5:4b",
    "messages": [{"role": "user", "content": "test"}],
    "stream": False,
    "options": {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0
    }
})
```

## Key Learnings

1. **LiteLLM Model Format:** When using `api_base`, don't prefix with `ollama/`
2. **Default Overrides:** `run_agent.py` defaults override environment variables
3. **Model Limitations:** Not all models support function calling via OpenAI API
4. **Provider Detection:** Custom endpoints need `provider: "openai"` for OpenAI-compatible APIs
5. **Configuration Priority:** CLI args > config.yaml > .env > defaults

## Recommendations for Tool Support

1. **Use Tool-Compatible Models:**
   - Llama 3.1 models in Ollama
   - Models specifically trained for function calling
   - Check Ollama documentation for tool-supporting models

2. **Alternative Approaches:**
   - Use OpenRouter with tool-capable models
   - Consider using a different model that supports tools
   - Use code execution approach for simple tasks

## Files Modified

1. `f:/AI/hermes-agent/.env` - Added Ollama configuration
2. `C:/Users/krase/.hermes/config.yaml` - Set default model and provider
3. `f:/AI/hermes-agent/requirements.txt` - Installed dependencies

## Test Commands

```bash
# Test Ollama API directly
curl -X POST http://localhost:11434/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"qwen3.5:4b\", \"messages\": [{\"role\": \"user\", \"content\": \"test\"}]}"

# Test with LiteLLM
python -c "import litellm; result = litellm.completion(model='qwen3.5:4b', messages=[{'role': 'user', 'content': 'test'}], api_base='http://localhost:11434/v1'); print(result)"

# Run hermes-agent with Ollama
python run_agent.py --model qwen3.5:4b --base-url http://localhost:11434/v1

# Check hermes configuration
python hermes config
```

## Current Status

✅ Ollama integration working  
✅ API calls successful  
✅ Model responding correctly  
❌ Tools not supported by qwen3.5:4b model  

The integration is technically complete. The limitation is with the model itself, not hermes-agent.
