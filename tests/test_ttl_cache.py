import pytest

from app.cache.ttl_cache import TTLCache


@pytest.mark.asyncio
async def test_ttl_cache_set_then_get():
    cache = TTLCache(ttl_seconds=1)
    await cache.set("london", {"temp_c": 10})

    value = await cache.get("london")

    assert value == {"temp_c": 10}
