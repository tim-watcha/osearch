import asyncio
from typing import List, Dict, Union, Literal

from aiohttp import ClientSession

from oracle_search.models.documents import WebContent, YoutubeTranscript
from oracle_search.models.base import SearchQuery
from oracle_search.pretty_logger import setup_logger
from oracle_search.conf.conf import Shared
from oracle_search.web_loader.web_loader import WebContentExtractor

logger = setup_logger()


async def afetch_results(query: SearchQuery) -> List[Dict[Literal["snippet", "title", "link"], str]]:
    search_params = {"dateRestrict": f"d{query.recent_days}"} if query.recent_days > 0 else {}
    return Shared.google_search.search_engine.results(query.query, num_results=3, search_params=search_params)


async def aget_search_results(queries: List[SearchQuery]) -> List[Dict[Literal["snippet", "title", "link"], str]]:
    tasks = [afetch_results(query) for query in queries]
    raw_results = await asyncio.gather(*tasks)
    all_results = [item for sublist in raw_results for item in sublist if "link" in item]
    return list({result["link"]: result for result in all_results}.values())


async def aget_search_full_contents(queries: list[SearchQuery]) -> List[Union[WebContent, YoutubeTranscript]]:
    all_results = await aget_search_results(queries)

    sources = list(set([result["link"] for result in all_results]))
    async with ClientSession() as session:
        tasks = [WebContentExtractor(url, session).afetch() for url in sources]
        contents = await asyncio.gather(*tasks)
    return [content for content in contents if content]
