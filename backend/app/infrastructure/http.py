import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def client(timeout: float = 15.0):
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as session:
        yield session
