#!/usr/bin/env python3
"""Debug script to check tool availability and model behavior"""

from model_tools import get_tool_definitions
from hermes_cli.runtime_provider import resolve_runtime_provider

# Check what tools are available
tools = get_tool_definitions(['file'], quiet_mode=True)
print(f"Available file tools ({len(tools)}):")
for tool in tools:
    print(f"  - {tool['function']['name']}")

# Check runtime provider config
runtime = resolve_runtime_provider(requested="custom:local (localhost:11434)")
print(f"\nRuntime provider: {runtime.get('provider')}")
print(f"Base URL: {runtime.get('base_url')}")
print(f"Model: {runtime.get('model')}")
print(f"Source: {runtime.get('source')}")
print(f"Full runtime dict: {runtime}")

# Test if we can create a simple agent call
from run_agent import AIAgent
runtime = resolve_runtime_provider(requested="custom:local (localhost:11434)")
print(f"\nCreating agent with:")
print(f"  model: qwen3.5:4b")
print(f"  api_key: {runtime.get('api_key')}")
print(f"  base_url: {runtime.get('base_url')}")
print(f"  provider: {runtime.get('provider')}")

agent = AIAgent(
    model="qwen3.5:4b",
    api_key=runtime.get("api_key"),
    base_url=runtime.get("base_url"),
    enabled_toolsets=['file'],
    quiet_mode=True
)

print("\nTesting simple tool call...")
response = agent.chat("Create a file called debug_test.txt with content 'test'")
print(f"Agent response: {response}")
