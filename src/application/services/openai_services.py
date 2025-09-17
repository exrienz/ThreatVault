import asyncio
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends
from openai import AsyncOpenAI, BadRequestError, NotFoundError, OpenAI

from src.application.exception.error import LLMException
from src.config import async_proxy_mounts, proxy_mounts
from src.persistence import FindingNameRepository, GlobalRepository


class OpenAIService:
    def __init__(
        self,
        repository: Annotated[GlobalRepository, Depends()],
        finding_repository: Annotated[FindingNameRepository, Depends()],
    ):
        self.repository = repository
        self.finding_repository = finding_repository

    async def get_conf(self):
        conf = await self.repository.get()
        if conf is None:
            raise
        if not conf.llm_url or not conf.llm_model:
            raise
        return conf

    async def get_client(self):
        conf = await self.repository.get()
        if conf is None:
            raise LLMException("Configuration Failed: Reach out to admin.")
        if not conf.llm_url or not conf.llm_model:
            raise LLMException("Please provide URL and Model!")
        return AsyncOpenAI(
            api_key=conf.llm_api_key,
            base_url=conf.llm_url,
            http_client=httpx.AsyncClient(mounts=async_proxy_mounts),
        ), conf

    async def streaming_cve(self, finding_id: UUID):
        client, conf = await self.get_client()
        finding = await self.finding_repository.get_by_id(finding_id)
        if finding is None:
            raise

        context = f"""
        Finding Name: {finding.name}
        Description:
            {finding.description}
        Solution:
            {finding.findings[0].remediation if len(finding.findings) > 0 else ""}
        """
        instructions = """
            You are an expert cybersecurity analyst.

            You will be given details of a security or system finding.
            Your tasks are:
            1. Gather and include any additional supporting information
                that helps explain the finding.
            2. Summarize all the information clearly and concisely.
            3. Write in a way that even a non-technical person can easily understand.
                Avoid jargon unless it’s absolutely necessary,
                and explain terms when used.
            4. Present your response in a structured format with these sections:
               - **Finding Name**
               - **Summary (non-technical explanation)**
               - **Impact (why this matters)**
               - **Recommended Solution**
        """
        model = conf.llm_model or ""
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": context},
                ],
                stream=True,
            )
            async for event in stream:
                yield {
                    "event": "message",
                    "data": event.choices[0].delta.content,
                }
        except (BadRequestError, NotFoundError) as e:
            msg = e.body
            if isinstance(msg, list):
                msg = msg[0]
            yield {"event": "message", "data": msg.get("error", {}).get("message")}
        finally:
            yield {"event": "close", "data": ""}

    async def test(self, msg: str):
        for event in [msg] * 10:
            await asyncio.sleep(1)
            yield {"event": "message", "data": event}

        yield {"event": "close", "data": ""}

    async def get_models(self, url: str, api_key: str):
        if not url:
            raise
        client = OpenAI(
            api_key=api_key, base_url=url, http_client=httpx.Client(mounts=proxy_mounts)
        )
        return [model.id.split("/")[-1] for model in client.models.list()]

    async def get_current_model(self):
        conf = await self.repository.get()
        if conf is None:
            return None
        return conf.llm_model

    # async def _validate_model(self, model: str): ...
