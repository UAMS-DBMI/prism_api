#!/usr/bin/env python3
import asyncpg
import asyncio
import sys

async def run():
    try:
        conn = await asyncpg.connect()
        await conn.close()
    except:
        sys.exit(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
