import asyncio
import traceback
from abc import ABC

from bs4 import BeautifulSoup
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By

from oracle_search.models.documents import WebContent
from oracle_search.pretty_logger import setup_logger

from oracle_search.web_loader.fetchers.base import WebContentFetcher, get_selenium_driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = setup_logger()


class GitHubFetcherBase(WebContentFetcher[WebContent], ABC):
    output_type = WebContent

    def __init__(self, url: str):
        super().__init__(url)
        self.driver = None

    async def _fetch_html(self):
        self.driver = get_selenium_driver()
        await asyncio.get_event_loop().run_in_executor(None, self.driver.get, self.url)
        await asyncio.get_event_loop().run_in_executor(None, self.driver.implicitly_wait, 10)

    async def _fetch_metadata(self) -> dict:
        metadata = {
            "title": self.driver.title,
            "description": None,
            "keywords": None,
            "published_date": None,
            "source": self.url,
        }

        published_date = None
        for _ in range(5):
            try:
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                last_commit_element = soup.find("relative-time")
                published_date = last_commit_element["datetime"]
            except TypeError:
                await asyncio.sleep(1)

        metadata["published_date"] = published_date
        return metadata

    async def _finalize(self):
        if self.driver:
            await asyncio.get_event_loop().run_in_executor(None, self.driver.quit)


class GitHubMarkdownFetcher(GitHubFetcherBase):
    async def _fetch_content(self) -> str:
        try:
            markdown_body = await asyncio.get_event_loop().run_in_executor(
                None,
                WebDriverWait(self.driver, 10).until,
                EC.visibility_of_element_located((By.CSS_SELECTOR, "article.markdown-body")),
            )
            content = markdown_body.get_attribute("innerHTML")
        except TimeoutException as e:
            trace = traceback.format_exc()
            logger.warning(f"Failed to extract GitHub Markdown content for {self.url}: {e}\n{trace}")
            content = None
        return content


class GitHubJupyterNotebookFetcher(GitHubFetcherBase):
    async def _fetch_content(self) -> str:
        try:
            iframe = await asyncio.get_event_loop().run_in_executor(
                None,
                WebDriverWait(self.driver, 10).until,
                EC.visibility_of_element_located((By.CSS_SELECTOR, "iframe")),
            )
            await asyncio.get_event_loop().run_in_executor(None, self.driver.switch_to.frame, iframe)

            content_div = await asyncio.get_event_loop().run_in_executor(
                None,
                WebDriverWait(self.driver, 10).until,
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div#notebook-container")),
            )
            content = content_div.get_attribute("innerHTML")
        except TimeoutException as e:
            logger.warning(f"Failed to extract GitHub Jupyter notebook content for {self.url}: {e}")
            content = None
        return content


class GitHubCodeBlobFetcher(GitHubFetcherBase):
    async def _fetch_content(self) -> str:
        await super()._fetch_html()
        try:
            textarea = await asyncio.get_event_loop().run_in_executor(
                None,
                WebDriverWait(self.driver, 10).until,
                EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea#read-only-cursor-text-area")),
            )
            content = textarea.get_attribute("value")
        except TimeoutException as e:
            logger.warning(f"Failed to extract GitHub code blob content for {self.url}: {e}")
            content = None
        return content
