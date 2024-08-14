import json
from typing import Union, List

from aiohttp import ClientSession
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import asyncio
from concurrent.futures import ThreadPoolExecutor
from textwrap import dedent
from oracle_search import Shared
from oracle_search.models.documents import WebContent, YoutubeTranscript
from oracle_search.pretty_logger import setup_logger
from oracle_search.web_loader.web_loader import WebContentExtractor

logger = setup_logger()


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
def web_task(url: str, task: str) -> Union[WebContent, YoutubeTranscript]:
    """
    Ask another AI assistant to answer a task to read or watch content from the given URL.

    Args:
        url (str): URL of the web page.
        task (str): The task to request to the AI assistant.

    Returns:
        Union[WebContent, YoutubeTranscript]: The answer of the task
    """

    async def fetch_and_qa(url: str, task: str):
        async with ClientSession() as session:
            extractor = WebContentExtractor(url, session)
            content = await extractor.afetch()
            return await web_qa(content, task)

    with ThreadPoolExecutor() as pool:
        return pool.submit(lambda: asyncio.run(fetch_and_qa(url, task))).result()


async def web_qa(content: Union[WebContent, YoutubeTranscript], task: str) -> Union[WebContent, YoutubeTranscript]:
    web_qa_template_prompt = dedent(
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
    web_qa_template = ChatPromptTemplate.from_messages([("system", web_qa_template_prompt), ("human", "{task}")])
    llm = ChatOpenAI(model=Shared.gpt.gpt_4o_mini, temperature=0.5)
    web_qa_chain = web_qa_template | llm
    res = (await web_qa_chain.ainvoke({"content": content.model_dump(), "task": task})).content
    content = content.model_copy()
    content.page_content = res
    return content


def answer_with_contents(contents: List[Union[WebContent, YoutubeTranscript]], task: str) -> str:
    def run_web_qa(content, request):
        return asyncio.run(web_qa(content, request))

    # Use ThreadPoolExecutor to run tasks concurrently
    with ThreadPoolExecutor() as executor:
        responses = list(executor.map(
            run_web_qa,
            contents,
            [task] * len(contents)
        ))

    web_qa_template_prompt = dedent(
        """\
        You are a helpful AI assistant designed to answer tasks based on specific content. Your goal is to provide accurate and relevant information from the given content.

        Here is the content you should use to answer task:

        <contents>
        {content}
        </contents>

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

    web_qa_template = ChatPromptTemplate.from_messages([("system", web_qa_template_prompt), ("human", "{task}")])

    llm = ChatOpenAI(model=Shared.gpt.gpt_4o, temperature=0.5)
    web_qa_chain = web_qa_template | llm
    res = web_qa_chain.invoke({"content": json.dumps([r.model_dump() for r in responses], ensure_ascii=False), "task": task})
    return res.content
