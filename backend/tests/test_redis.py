"""Redis cache latency test."""
import time

from core.cache import get_cached_response, cache_response, flush_all_cache

print("Testing Redis...")

start = time.time()
cache_response("test query audit", "test response audit")
write_time = time.time() - start
print(f"Write time: {write_time:.2f}s")

start = time.time()
result = get_cached_response("test query audit")
read_time = time.time() - start
print(f"Read time: {read_time:.2f}s")
print(f"Got cached: {result == 'test response audit'}")

flush_all_cache()
print(f"Redis region recommendation: {'OK' if read_time < 0.5 else 'SLOW - consider Singapore region'}")
