import asyncio
import sys

if sys.platform.startswith("win"):
    loop = asyncio.SelectorEventLoop()
else:
    loop = asyncio.new_event_loop()

print(type(loop))