import pytest
import asyncio
from application.events.event_bus import EventBus


@pytest.mark.asyncio
async def test_event_bus_publish_receive():
    bus = EventBus()
    queue = bus.subscribe("exec-1")

    await bus.publish("exec-1", {"event_type": "TEST", "data": "hello"})

    event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert event["event_type"] == "TEST"
    assert event["data"] == "hello"


@pytest.mark.asyncio
async def test_event_bus_no_subscribers():
    bus = EventBus()
    # Should not raise even with no subscribers
    await bus.publish("exec-999", {"event_type": "TEST"})


@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus()
    queue = bus.subscribe("exec-1")
    bus.unsubscribe("exec-1", queue)

    await bus.publish("exec-1", {"event_type": "TEST"})
    assert queue.empty()


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    bus = EventBus()
    q1 = bus.subscribe("exec-1")
    q2 = bus.subscribe("exec-1")

    await bus.publish("exec-1", {"event_type": "TEST"})

    e1 = await asyncio.wait_for(q1.get(), timeout=1.0)
    e2 = await asyncio.wait_for(q2.get(), timeout=1.0)
    assert e1["event_type"] == "TEST"
    assert e2["event_type"] == "TEST"
