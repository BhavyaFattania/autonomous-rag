"""
Platform-specific event loop setup for testing async behaviors.

Demonstrates proper event loop initialization for Windows vs Unix platforms.
Useful for debugging async compatibility issues during development.

Usage:
    python scripts/test_loop.py
"""

import asyncio
import sys

if sys.platform.startswith("win"):
    loop = asyncio.SelectorEventLoop()
else:
    loop = asyncio.new_event_loop()

print(type(loop))
