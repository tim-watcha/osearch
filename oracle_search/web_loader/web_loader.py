
from typing import Union, Optional
from urllib.parse import urlparse

from aiohttp import ClientSession
from oracle_search.models.documents import YoutubeTranscript, WebContent
from oracle_search.web_loader.fetchers.base import YOUTUBE_REGEX, DefaultWebFetcher
from oracle_search.web_loader.fetchers.github import (
    GitHubJupyterNotebookFetcher,
    GitHubMarkdownFetcher,
    GitHubCodeBlobFetcher,
)
from oracle_search.web_loader.fetchers.namu_wiki import NamuWikiFetcher
from oracle_search.web_loader.fetchers.naver import NaverBlogFetcher
from oracle_search.web_loader.fetchers.youtube import YouTubeFetcher


class ContentFetcherFactory:
    @staticmethod
    def create_fetcher(url: str, session: Optional[ClientSession] = None):
        parsed_url = urlparse(url)
        if YOUTUBE_REGEX.search(url):
            return YouTubeFetcher(url)
        elif "github.com" in parsed_url.netloc and "blob" in parsed_url.path:
            if parsed_url.path.endswith(".ipynb"):
                return GitHubJupyterNotebookFetcher(url)
            elif parsed_url.path.endswith(".md"):
                return GitHubMarkdownFetcher(url)
            else:
                return GitHubCodeBlobFetcher(url)
        elif "namu.wiki" in parsed_url.netloc:
            return NamuWikiFetcher(url, session)
        elif "blog.naver.com" in parsed_url.netloc:
            return NaverBlogFetcher(url, session)
        return DefaultWebFetcher(url, session)


class WebContentExtractor:
    """
    URL로부터 웹 콘텐츠를 가져오는 클래스입니다.
    """

    def __init__(self, url: str, session: ClientSession):
        self.fetcher = ContentFetcherFactory.create_fetcher(url, session)

    async def afetch(self, refresh=False) -> Union[WebContent, YoutubeTranscript]:
        return await self.fetcher.fetch(refresh=refresh)

    def fetch(self) -> Union[WebContent, YoutubeTranscript]:
        # return asyncio.run(self.afetch())
        # ThreadPoolExecutor 안에서 asyncio.run을 사용할 수 없으므로 일단 봉인
        pass

