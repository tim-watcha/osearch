from datetime import datetime
from textwrap import dedent
from typing import Union, List

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from oracle_search import Shared
from oracle_search.models.base import RedefinedRequest, GeneratedQuery
from oracle_search.models.documents import WebContent, YoutubeTranscript


def get_current_datetime_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_refined_request(content: Union[WebContent, YoutubeTranscript], request: str) -> RedefinedRequest:
    prompt = dedent("""\
        You are given Content and Request. You are tasked with redefine the request to be specific to avoid ambiguity and provide a clear and concise question from the given content and request.
        Use the content as background information to refine the request. The refined request should be self-contained and clear.
        Current datetime is: {datetime}
        """)

    llm = ChatOpenAI(model=Shared.gpt.gpt_4o, temperature=0.5)
    template = ChatPromptTemplate.from_messages(
        [("system", prompt), ("human", "Content: {content}\n\nHere is the Request you need to redefine: {request}")])
    chain = template | llm.with_structured_output(RedefinedRequest, method="json_schema")
    return chain.invoke({"content": content.model_dump(), "request": request, "datetime": get_current_datetime_string()})


def get_search_query(chat_history: List[BaseMessage]) -> GeneratedQuery:
    prompt = dedent("""\
        You are given a refined request from 'HUMAN'. Your task is to generate a list of search queries based on the Request. The search queries should be specific and relevant to the request.
        You should use relevant language and terms to ensure the search queries are effective in retrieving accurate information.
        
        # Guidelines
        1. Improve the search effectiveness by suggesting expansion terms for the query
        2. Recommend expansion terms for the query to improve search results
        3. Improve the search effectiveness by suggesting useful expansion terms for the query
        4. Maximize search utility by suggesting relevant expansion phrases for the query
        5. Enhance search efficiency by proposing valuable terms to expand the query
        6. Elevate search performance by recommending relevant expansion phrases for the query
        7. Boost the search accuracy by providing helpful expansion terms to enrich the query
        8. Increase the search efficacy by offering beneficial expansion keywords for the query
        9. Optimize search results by suggesting meaningful expansion terms to enhance the query
        10. Enhance search outcomes by recommending beneficial expansion terms to supplement the query
        11. Translate the query into the language of the country most likely to yield relevant search results
        
        Now, list the languages that are most likely relevant to the result and generate search queries based on the Request.
        """)

    llm = ChatOpenAI(model=Shared.gpt.gpt_4o, temperature=0.5)
    template = ChatPromptTemplate.from_messages(
        [("system", prompt), MessagesPlaceholder(variable_name='chat_history')])
    chain = template | llm.with_structured_output(GeneratedQuery, method="json_schema", include_raw=True)
    return chain.invoke({'chat_history': chat_history})
