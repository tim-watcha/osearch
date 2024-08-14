import operator
from typing import Annotated, Optional, Union, TypedDict

from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.constants import END
from langgraph.graph import add_messages, StateGraph
from pydantic import BaseModel

from App import fetch_url_content
from oracle_search.chain.base import get_refined_request, get_search_query
from oracle_search.models.documents import WebContent, YoutubeTranscript
from oracle_search.web_loader.search import aget_search_full_contents


class OracleState(TypedDict):
    url: Optional[str]
    task_description: str
    chat_history: Annotated[list[BaseMessage], add_messages]
    dp_history: Annotated[list[BaseModel], operator.add]
    search_results: Optional[list[Union[WebContent, YoutubeTranscript]]]
    total_cost: Annotated[float, operator.add]


async def begin(state: OracleState):
    with get_openai_callback() as cb:
        if state['url'] is None:
            task_description = state['task_description']
        else:
            content = await fetch_url_content(state['url'])
            task_description = get_refined_request(content, state['task_description']).redefined_request
    return {
        "task_description": task_description,
        "chat_history": [HumanMessage(content=task_description, additional_kwargs={"name": "HUMAN"})],
        "dp_history": [HumanMessage(content=task_description, additional_kwargs={"name": "HUMAN"})],
        'total_cost': cb.total_cost
    }


async def generate_query_and_search(state: OracleState):
    with get_openai_callback() as cb:
        query_res = get_search_query(state['chat_history'])
        query_message = query_res['raw']
        query_message.additional_kwargs['name'] = 'QUERYGENERATOR'
        query_parsed = query_res['parsed']

        search_results = await aget_search_full_contents(query_parsed.queries)
        mock_search_message = HumanMessage(content=f"{len(search_results)} web contents are stored in Long Term Memory",
                                           additional_kwargs={"name": "SEARCH"})
    return {
        "chat_history": [query_message, mock_search_message],
        "dp_history": [query_parsed, mock_search_message],
        "search_results": search_results,
        'total_cost': cb.total_cost
    }


def get_graph():
    graph = StateGraph(OracleState)
    graph.add_node("Begin", begin)
    graph.add_node("Search", generate_query_and_search)
    graph.add_edge("Begin", "Search")
    graph.add_edge("Search", END)
    graph.set_entry_point("Begin")

    return graph.compile()
    # graph.add_conditional_edges(
    #     "AnswerWithLongTermMemory",
    #     chat_router,
    #     {
    #         "answer_with_long_term_memory": "MockNodeBeforeAnswer",
    #         "answering": "MockNodeBeforeAnswer",
    #         "plan": "Refine",
    #     },
    # )
