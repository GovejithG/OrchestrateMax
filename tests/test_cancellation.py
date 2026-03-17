import pytest
import asyncio
from application.agent.cancellation_token import CancellationToken


def test_cancellation_token_initial_state():
    token = CancellationToken()
    assert not token.is_cancelled()


def test_cancellation_token_cancel():
    token = CancellationToken()
    token.cancel()
    assert token.is_cancelled()


def test_cancellation_token_idempotent():
    token = CancellationToken()
    token.cancel()
    token.cancel()
    assert token.is_cancelled()


@pytest.mark.asyncio
async def test_cancellation_token_wait():
    token = CancellationToken()

    async def cancel_after():
        await asyncio.sleep(0.05)
        token.cancel()

    asyncio.create_task(cancel_after())
    await asyncio.wait_for(token.wait(), timeout=1.0)
    assert token.is_cancelled()
