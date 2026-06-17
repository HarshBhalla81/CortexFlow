import redis

from watchdog.watchdog import BDHWatchdog
redis_client = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)
watchdog = BDHWatchdog(redis_client)
watchdog.run_csv()