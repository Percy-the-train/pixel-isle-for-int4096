import asyncio
import random
import time

import httpx

from app.delay import (JobControl, RequestGateway, calc_wait, describe_ranges, normalize_delay,
                       safety, wait_ranges)

CFG = {"base": 10, "variation": True, "var_min": 1, "var_max": 5, "direction": "both", "floor": 1}


def test_both_directions_stay_in_expected_ranges():
    rng = random.Random(1)
    for _ in range(1000):
        w = calc_wait(CFG, rng)
        assert (5 <= w <= 9) or (11 <= w <= 15)


def test_plus_and_minus_only():
    rng = random.Random(2)
    assert all(11 <= calc_wait({**CFG, "direction": "plus"}, rng) <= 15 for _ in range(200))
    assert all(5 <= calc_wait({**CFG, "direction": "minus"}, rng) <= 9 for _ in range(200))


def test_floor_prevents_negative_or_tiny_waits():
    cfg = {**CFG, "base": 2, "direction": "minus", "floor": 1}
    assert all(calc_wait(cfg, random.Random(i)) >= 1 for i in range(200))


def test_no_variation_is_constant():
    cfg = {**CFG, "variation": False}
    assert {calc_wait(cfg) for _ in range(20)} == {10.0}


def test_ranges_and_description():
    assert wait_ranges(CFG) == [(5, 9), (11, 15)]
    assert describe_ranges(CFG) == "5–9s or 11–15s"
    assert describe_ranges({**CFG, "direction": "plus"}) == "11–15s"


def test_min_max_are_swapped_when_reversed():
    c = normalize_delay({"var_min": 5, "var_max": 1})
    assert (c["var_min"], c["var_max"]) == (1, 5)


def test_invalid_values_fall_back_to_defaults():
    c = normalize_delay({"base": "abc", "direction": "sideways"})
    assert c["base"] == 10.0 and c["direction"] == "both"


def test_safety_levels():
    assert safety(CFG)["level"] == "green"
    assert safety({"base": 4, "variation": False})["level"] == "yellow"
    assert safety({"base": 1, "variation": False})["level"] == "red"


def test_gateway_never_sends_faster_than_delay():
    stamps = []

    def handler(request):
        stamps.append(time.monotonic())
        return httpx.Response(200, text="ok")

    async def run():
        gw = RequestGateway({"base": 0.3, "variation": False, "floor": 0.3}, JobControl(),
                            client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        try:
            for _ in range(3):
                await gw.fetch("https://example.test/")
        finally:
            await gw.aclose()

    asyncio.run(run())
    assert len(stamps) == 3
    assert all(b - a >= 0.28 for a, b in zip(stamps, stamps[1:]))


def test_gateway_backs_off_on_429_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(429 if calls["n"] == 1 else 200, text="x")

    async def run():
        gw = RequestGateway({"base": 0.05, "variation": False, "floor": 0.05}, JobControl(),
                            client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), retries=2)
        try:
            r = await gw.fetch("https://example.test/")
            return r.status_code, gw.request_count
        finally:
            await gw.aclose()

    status, count = asyncio.run(run())
    assert status == 200 and count == 2