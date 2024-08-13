from aiohttp import ClientSession

from oracle_search.web_loader.fetchers.base import DefaultWebFetcher, html_to_markdown
from oracle_search.pretty_logger import setup_logger

logger = setup_logger()


class NaverBlogFetcher(DefaultWebFetcher):
    def __init__(self, url: str, session: ClientSession):
        if "/blog.naver.com/" in url:
            # 네이버 블로그 URL을 모바일 버전으로 변경
            url = url.replace("/blog.naver.com/", "/m.blog.naver.com/")
        super().__init__(url, session)

    async def _fetch_content(self) -> str:
        if not self.soup:
            await self._fetch_html()

        if content_div := (
            self.soup.find("div", {"class": "se-main-container"}) or self.soup.find("div", {"class": "_postView"})
        ):
            return str(content_div)
        else:
            logger.warning(f"Failed to find the content div with class 'se-main-container' in {self.url}")
            return ""

    async def _post_process(self, content) -> str:
        return html_to_markdown(content, include_images=True, include_links=True)
