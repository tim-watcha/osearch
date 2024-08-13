import asyncio
import traceback

from htmldate import find_date
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from youtube_transcript_api import YouTubeTranscriptApi

from oracle_search.models.documents import YoutubeTranscript
from oracle_search.web_loader.fetchers.base import WebContentFetcher, get_selenium_driver, logger, YOUTUBE_REGEX


class YouTubeFetcher(WebContentFetcher[YoutubeTranscript]):
    output_type = YoutubeTranscript

    def __init__(self, url: str):
        super().__init__(url)
        self.driver = None

    async def _fetch_html(self):
        self.driver = get_selenium_driver()
        await asyncio.get_event_loop().run_in_executor(None, self.driver.get, self.url)

        try:
            expand_button = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div#snippet"))
                ),
            )
            expand_button.click()
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Failed to expand YouTube description: {e}")

        self.html = self.driver.page_source

    async def _post_process(self, content) -> str:
        return content

    async def _fetch_content(self) -> str:
        match = YOUTUBE_REGEX.search(self.url)
        if match:
            video_id = match.group(1)
            try:
                transcript = await asyncio.get_event_loop().run_in_executor(
                    None, YouTubeTranscriptApi.get_transcript, video_id, ["ko", "en", "ja"]
                )
                return " ".join([line["text"] for line in transcript])
            except Exception as e:
                logger.error(f"Failed to fetch transcript for {self.url}: {e}")
                return ""
        return ""

    async def _fetch_metadata(self) -> dict:
        try:
            # Wait for the title element to be present
            title_element = await asyncio.get_event_loop().run_in_executor(
                None,
                WebDriverWait(self.driver, 10).until,
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#title h1 yt-formatted-string")),
            )
            title = title_element.text

            description_header = self.driver.find_element(
                By.CSS_SELECTOR, "ytd-watch-info-text#ytd-watch-info-text"
            ).text
            description_body = self.driver.find_element(
                By.CSS_SELECTOR, "ytd-text-inline-expander#description-inline-expander yt-attributed-string"
            ).text
            description = f"{description_header}\n{description_body}"

            channel_element = self.driver.find_element(
                By.CSS_SELECTOR, "ytd-channel-name#channel-name yt-formatted-string a"
            )
            channel_name = channel_element.text

            published_date = find_date(self.html)

            metadata = {
                "title": title,
                "description": description,
                "channel_name": channel_name,
                "keywords": self.driver.find_element(By.CSS_SELECTOR, 'meta[name="keywords"]').get_attribute("content"),
                "published_date": published_date,
                "source": self.url,
            }
        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Failed to extract YouTube metadata for {self.url}: {e}\n{trace}")
            metadata = {"error": "Failed to extract metadata"}
        finally:
            if self.driver:
                await asyncio.get_event_loop().run_in_executor(None, self.driver.quit)

        return metadata

    async def _finalize(self):
        if self.driver:
            self.driver.quit()

    async def _fetch(self) -> YoutubeTranscript:
        if not self.html:
            await self._fetch_html()
        content = await self._fetch_content()
        metadata = await self._fetch_metadata()
        metadata["summary"] = None
        return YoutubeTranscript(page_content=content, source=self.url, metadata=metadata)
