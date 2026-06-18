import asyncio
from watchdog.watchdog import BDHWatchdog

print("[WATCHDOG RUNNER] Booting up neural watchdog (async mode)...")
watchdog = BDHWatchdog()
asyncio.run(watchdog.run_csv())