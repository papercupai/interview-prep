"""
Citi drill: a resilient async LLM call path in Python (FastAPI + asyncio).
Type it from memory in about 15 minutes. Run it to self-test: python3 citi-async-drill.py
"""

import asyncio
import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class TransientError(Exception):   # 429, 503, network blip: worth retrying
    pass


class PermanentError(Exception):   # 400, content filter, bad auth: retrying won't help
    pass


class AllProvidersFailed(Exception):
    pass


class ModelRouter:
    """Ordered fallback across providers, retries with jittered backoff,
    a per-call timeout, and a cap on concurrent calls (rate limits and cost)."""

    def __init__(self, providers, max_concurrency=8, timeout_s=20.0, retries=2, backoff_s=0.5):
        self.providers = providers  # each has: async complete(prompt) -> str
        self.sem = asyncio.Semaphore(max_concurrency)
        self.timeout_s, self.retries, self.backoff_s = timeout_s, retries, backoff_s

    async def complete(self, prompt: str) -> str:
        async with self.sem:
            last = None
            for provider in self.providers:              # routing = ordered fallback
                for attempt in range(self.retries + 1):
                    try:
                        return await asyncio.wait_for(provider.complete(prompt), self.timeout_s)
                    except (asyncio.TimeoutError, TransientError) as e:
                        last = e                         # jitter avoids a retry stampede
                        await asyncio.sleep(self.backoff_s * 2 ** attempt * random.uniform(0.5, 1.5))
                    except PermanentError as e:
                        last = e
                        break                            # don't retry; try the next provider
            raise AllProvidersFailed(repr(last))


async def run_tools(calls, timeout_s=10.0):
    """Fan out independent tool calls; one failure must not sink the others."""
    results = await asyncio.gather(*(asyncio.wait_for(c, timeout_s) for c in calls),
                                   return_exceptions=True)
    return [r if not isinstance(r, BaseException) else {"error": type(r).__name__} for r in results]


class Ask(BaseModel):
    prompt: str


def make_app(router: ModelRouter) -> FastAPI:
    app = FastAPI()

    @app.post("/ask")
    async def ask(body: Ask) -> dict:
        try:
            return {"answer": await router.complete(body.prompt)}
        except AllProvidersFailed:
            raise HTTPException(status_code=503, detail="all model providers unavailable")

    return app


# ---- self-test ----
if __name__ == "__main__":
    class Flaky:
        def __init__(self, fails, error=TransientError, delay=0.0, reply="ok"):
            self.fails, self.error, self.delay, self.reply, self.calls = fails, error, delay, reply, 0

        async def complete(self, prompt):
            self.calls += 1
            await asyncio.sleep(self.delay)
            if self.calls <= self.fails:
                raise self.error("boom")
            return f"{self.reply}:{prompt}"

    async def main():
        r = ModelRouter([Flaky(2)], backoff_s=0)                   # 2 transient failures, then success
        assert await r.complete("hi") == "ok:hi"
        bad, backup = Flaky(99, PermanentError), Flaky(0, reply="backup")
        r = ModelRouter([bad, backup], backoff_s=0)
        assert await r.complete("x") == "backup:x" and bad.calls == 1   # permanent: no retries
        slow = Flaky(0, delay=1.0)
        r = ModelRouter([slow, Flaky(0, reply="fast")], timeout_s=0.05, retries=1, backoff_s=0)
        assert await r.complete("y") == "fast:y" and slow.calls == 2     # timeouts are retried
        r = ModelRouter([Flaky(99)], retries=1, backoff_s=0)
        try:
            await r.complete("z")
            raise AssertionError("expected AllProvidersFailed")
        except AllProvidersFailed:
            pass
        async def ok():
            return 1
        async def boom():
            raise ValueError
        assert await run_tools([ok(), boom(), asyncio.sleep(5)], timeout_s=0.05) == \
            [1, {"error": "ValueError"}, {"error": "TimeoutError"}]
        # concurrency cap: 5 calls through a cap of 2 never overlap more than 2
        live = peak = 0
        class Counting:
            async def complete(self, prompt):
                nonlocal live, peak
                live += 1; peak = max(peak, live)
                await asyncio.sleep(0.01)
                live -= 1
                return prompt
        r = ModelRouter([Counting()], max_concurrency=2)
        await asyncio.gather(*(r.complete(str(i)) for i in range(5)))
        assert peak == 2

    asyncio.run(main())
    app = make_app(ModelRouter([Flaky(0)]))
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        assert client.post("/ask", json={"prompt": "hi"}).json() == {"answer": "ok:hi"}
        down = TestClient(make_app(ModelRouter([Flaky(99, PermanentError)])))
        assert down.post("/ask", json={"prompt": "hi"}).status_code == 503
    except ImportError:          # TestClient needs httpx; the router tests above still ran
        print("(skipped HTTP checks: pip install httpx)")
    print("citi-async-drill: all checks passed")
