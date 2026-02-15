import asyncio

import pytest

from app.cache.ttl_cache import TTLCache


@pytest.mark.asyncio
async def test_ttl_cache_returns_value_before_expiry():
    cache = TTLCache(ttl_seconds=1)
    await cache.set("london", {"temp_c": 10})

    value = await cache.get("london")

    assert value == {"temp_c": 10}


@pytest.mark.asyncio
async def test_ttl_cache_expires_value():
    cache = TTLCache(ttl_seconds=0.05)
    await cache.set("london", {"temp_c": 10})

    await asyncio.sleep(0.08)
    value = await cache.get("london")

    assert value is None
