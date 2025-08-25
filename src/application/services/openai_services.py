import asyncio
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI, BadRequestError, OpenAI

from src.persistence import GlobalRepository


class OpenAIService:
    def __init__(self, repository: Annotated[GlobalRepository, Depends()]):
        self.repository = repository

    async def get_conf(self):
        conf = await self.repository.get()
        if conf is None:
            raise
        if not conf.llm_url or not conf.llm_model:
            raise
        return conf

    async def streaming(self, msg: str):
        conf = await self.repository.get()
        if conf is None:
            raise
        if not conf.llm_url or not conf.llm_model:
            raise

        client = AsyncOpenAI(api_key=conf.llm_api_key)

        stream = await client.responses.create(
            model=conf.llm_model,
            instructions="""
            You are a CyberSecurity expert explaining vulnerability
            to a non-technical person
            """,
            input=msg,
            stream=True,
        )
        async for event in stream:
            yield {"event": "message", "data": event}

    async def test(self, msg: str):
        for event in [msg] * 10:
            await asyncio.sleep(1)
            yield {"event": "message", "data": event}

        yield {"event": "close", "data": ""}

    async def get_models(self, url: str, api_key: str):
        if not url:
            raise
        client = OpenAI(api_key=api_key, base_url=url)
        try:
            return client.models.list()
        except BadRequestError:
            raise

    async def get_current_model(self):
        conf = await self.repository.get()
        if conf is None:
            return None
        return conf.llm_model

    # async def _validate_model(self, model: str): ...
