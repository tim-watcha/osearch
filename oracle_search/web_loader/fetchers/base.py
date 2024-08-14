import platform
import re
import traceback
from abc import ABC, abstractmethod
from functools import wraps
from typing import Union, TypeVar, Generic, Type

import trafilatura
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from htmldate import find_date
from readability import Document
from selenium import webdriver
import html2text

from oracle_search import Shared
from oracle_search.pretty_logger import setup_logger

from oracle_search.models.documents import WebContent, YoutubeTranscript
from datetime import timedelta


logger = setup_logger()

YOUTUBE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=)?(.+)")


def get_selenium_driver():
    # TODO: 드라이버를 매번 로드하지 않도록 수정하여 속도를 빠르게
    if "linux" in platform.system().lower():
        # Set up Firefox options
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Set up the Gecko driver
        service = webdriver.FirefoxService("/usr/local/bin/geckodriver")
        driver = webdriver.Firefox(service=service, options=options)
    else:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
    return driver


def html_to_markdown(html: str, include_images: bool = False, include_links: bool = True) -> str:
    """
    HTML을 마크다운으로 변환합니다.

    Args:
        html (str): 변환할 HTML 문자열.
        include_images (bool): 이미지를 포함할지 여부.
        include_links (bool): 링크를 포함할지 여부.

    Returns:
        str: 마크다운 형식의 문자열.
    """
    h = html2text.HTML2Text()
    h.ignore_links = not include_links
    h.ignore_images = not include_images
    h.skip_internal_links = True
    h.bypass_tables = False
    h.mark_code = True
    h.escape_snob = True
    h.body_width = 0  # 텍스트 줄바꿈 비활성화
    return "\n".join([line.strip() for line in h.handle(html).split("\n")])


T = TypeVar("T", bound=Union[WebContent, YoutubeTranscript])


def cached_fetch(func):
    @wraps(func)
    async def wrapper(self, *args, refresh=False, **kwargs):
        web_cache = Shared.disk_cache.web_cache
        cache_key = f"{self.__class__.__name__}:{self.url}"

        if not refresh:
            cached_result = web_cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {self.url}")
                return self.output_type.validate(cached_result)

        result = await func(self, *args, **kwargs)
        if result is not None:
            try:
                web_cache.set(cache_key, result.dict(), expire=timedelta(days=1).total_seconds())
                logger.info(f"{'Refreshed' if refresh else 'Cached'} result for {self.url}")
            except Exception as e:
                trace = traceback.format_exc()
                logger.error(f"Failed to cache result for {self.url}: {e}\n{trace}")

        return result

    return wrapper


class WebContentFetcher(ABC, Generic[T]):
    """
    웹 콘텐츠를 가져오는 기본 클래스입니다.
    각자의 기능에 맞게 이 클래스를 상속하여 구현해야 합니다.
    _가 붙은 method를 상황에 맞게 구현합니다.

    메서드 실행 순서:
    fetch -> _fetch -> _fetch_html -> html fetch 됨
                    -> _fetch_content -> post_process -> html로부터 contents 부분의 html을 가져온 후 md로 변환
                    -> _fetch_metadata -> html로부터 metadata를 가져옴
                        -> WebContent 또는 YoutubeTranscript 객체 리턴
                         -> _finalize -> fetch 작업 완료 후 필요한 정리 작업 수행 (e.g. driver 종료)

    """

    output_type: Type[T]

    def __init__(self, url: str):
        self.url = url
        self.html = None
        self.soup = None
        self.content = None

    @abstractmethod
    async def _fetch_html(self):
        """
        self.url 에서 HTML 컨텐츠를 가져옵니다.
        """
        pass

    @staticmethod
    async def _post_process(content) -> str:
        """
        콘텐츠 후처리 메서드입니다. 기본적으로 HTML 을 마크다운 형식으로 변환합니다.
        """

        md = html_to_markdown(content)
        return md

    @abstractmethod
    async def _fetch_content(self) -> str:
        """
        self.html 에서 직접 콘텐츠를 가져옵니다.
        self._fetch_html 이 수행된 후에 실행되어야 합니다.
        """
        pass

    async def fetch_content(self) -> str:
        return await self._post_process(await self._fetch_content())

    @abstractmethod
    async def _fetch_metadata(self) -> dict:
        """
        self.html 에서 메타데이터를 가져옵니다. self._fetch_html 이 수행된 후에 실행되어야 합니다.
        """
        pass

    @abstractmethod
    async def _finalize(self):
        """
        fetch 작업 후 정리 작업을 수행합니다. (e.g. driver 종료)
        """
        pass

    async def _fetch(self) -> T:
        """
        self.url 에서 콘텐츠와 메타데이터를 가져와 WebContent 또는 YoutubeTranscript 형식으로 반환합니다.
        fetch 메서드를 실행할 때 이 메서드가 호출됩니다.
        """
        if not self.html:
            await self._fetch_html()
        metadata = await self._fetch_metadata()
        content = await self.fetch_content()
        metadata["summary"] = None
        return WebContent(page_content=content, source=self.url, metadata=metadata)

    @cached_fetch
    async def fetch(self, refresh: bool = False) -> T:
        """
        콘텐츠를 가져오는 주요 메서드입니다.
        먼저 이전에 컨텐츠를 가져온 적이 있으면 바로 반환하고, 그렇지 않으면 _fetch 메서드를 호출하여 콘텐츠를 가져옵니다.
        """
        try:
            if self.content:
                return self.content
            self.content = await self._fetch()
        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Failed to fetch content for {self.url}: {e}\n{trace}")
        finally:
            await self._finalize()
        return self.content


class DefaultWebFetcher(WebContentFetcher[WebContent]):
    """
    특별한 Fetcher가 지정되지 않은 URL에 대해 Fall-back으로 사용되는 Fetcher입니다.
    """

    output_type = WebContent

    def __init__(self, url: str, session: ClientSession):
        super().__init__(url)
        self.session = session

    async def _fetch_html(self):
        async with self.session.get(self.url) as response:
            self.html = await response.text()
        self.soup = BeautifulSoup(self.html, "html.parser")

    async def _post_process(self, content) -> str:
        return content

    async def _fetch_content(self) -> str:
        """
        readability와 trafilatura를 사용하여 콘텐츠를 추출합니다.
        둘 중 더 긴 콘텐츠를 반환합니다.
        """
        readability_content = html_to_markdown(Document(self.html).summary())
        trafilatura_content = trafilatura.extract(self.html, output_format="markdown")

        if readability_content and trafilatura_content and len(readability_content) > len(trafilatura_content):
            return readability_content
        elif trafilatura_content:
            return trafilatura_content
        else:
            # TODO: 이렇게 해도 동적으로 로드되는 페이지를 가져올 수 없는 경우가 있는데, 이 때 selenium을 사용하도록 수정해야합니다. (예: 조선일보)
            return html_to_markdown(self.html)

    async def _fetch_metadata(self) -> dict:
        metadata = {
            "title": self.soup.find("title").text if self.soup.find("title") else None,
            "description": self.soup.find("meta", {"name": "description"})["content"]
            if self.soup.find("meta", {"name": "description"})
            else None,
            "keywords": self.soup.find("meta", {"name": "keywords"})["content"]
            if self.soup.find("meta", {"name": "keywords"})
            else None,
            "published_date": find_date(self.html),
            "source": self.url,
        }
        return metadata

    async def _finalize(self):
        return
