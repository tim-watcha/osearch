from typing import Union

from aiohttp import ClientSession
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import asyncio
from concurrent.futures import ThreadPoolExecutor
from textwrap import dedent
from oracle_search import Shared
from oracle_search.models.documents import WebContent, YoutubeTranscript
from oracle_search.web_loader.web_loader import WebContentExtractor


@tool
def get_web_content(url: str) -> Union[WebContent, YoutubeTranscript]:
    """
    Get content and metadata of a web page or a YouTube video from the given URL.

    Args:
        url (str): URL of the web page.

    Returns:
        Union[WebContent, YoutubeTranscript]: The web content.
    """

    async def fetch_content(url: str):
        async with ClientSession() as session:
            extractor = WebContentExtractor(url, session)
            return await extractor.afetch()

    with ThreadPoolExecutor() as pool:
        content = pool.submit(lambda: asyncio.run(fetch_content(url))).result()

    return content


@tool
def web_task(url: str, task: str) -> str:
    """
    Ask another AI assistant to answer a task to read or watch content from the given URL.

    Args:
        url (str): URL of the web page.
        task (str): The task to request to the AI assistant.

    Returns:
        str: The answer of the task
    """

    async def fetch_content(url: str):
        async with ClientSession() as session:
            extractor = WebContentExtractor(url, session)
            return await extractor.afetch()

    with ThreadPoolExecutor() as pool:
        content = pool.submit(lambda: asyncio.run(fetch_content(url))).result()

    web_qa_prompt_text = dedent(
        """\
        You are a helpful AI assistant designed to answer tasks based on specific content. Your goal is to provide accurate and relevant information from the given content.

        Here is the content you should use to answer task:

        <content>
        {content}
        </content>

        When given a task, follow these instructions:

        1. Carefully read and understand the task.
        2. Search the provided content for relevant information.
        3. If you find information in the content that directly answers the task, use it to formulate your response.
        4. If the content does not contain information relevant to the task, or if you are unsure about the answer, you must respond with "I don't know."
        5. Do not use any external knowledge or information not present in the given content.
        6. Provide concise and accurate answers based solely on the information in the content.

        Remember, your responses should be based exclusively on the information in the provided content. Do not speculate or provide information from other sources.
        The user will now provide you with task.
        """
    )
    web_qa_prompt = ChatPromptTemplate.from_messages([("system", web_qa_prompt_text), ("human", "{task}")])
    llm = ChatOpenAI(model=Shared.gpt.gpt_4o, temperature=0.2)
    web_qa_chain = web_qa_prompt | llm

    return web_qa_chain.invoke({"content": content.dict(), "task": task}).content
