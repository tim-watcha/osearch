from aiohttp import ClientSession

from oracle_search.web_loader.fetchers.base import DefaultWebFetcher, html_to_markdown
from oracle_search.pretty_logger import setup_logger

logger = setup_logger()


class NamuWikiFetcher(DefaultWebFetcher):
    def __init__(self, url: str, session: ClientSession):
        super().__init__(url, session)

    async def _fetch_content(self) -> str:
        if not self.soup:
            await self._fetch_html()

        h1_tag = self.soup.find("h1")
        if h1_tag:
            content_div = h1_tag.find_parent("div")
            for _ in range(2):
                content_div = content_div.find_parent("div")
            if content_div:
                return str(content_div)
            else:
                logger.warning(f"Failed to find the content div in {self.url}")
                return ""
        else:
            logger.warning(f"Failed to find the <h1> tag in {self.url}")
            return ""

    async def _post_process(self, content) -> str:
        return html_to_markdown(content, include_images=True, include_links=True)
