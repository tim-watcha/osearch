import os
from functools import cached_property
from typing import Optional

from diskcache import Cache
from langchain_google_community import GoogleSearchAPIWrapper


class GPT:
    gpt_35: str
    gpt_4: str
    gpt_4o: str

    def __init__(self, config: dict[str, any]):
        self.gpt_35 = config["models"]["gpt35"]
        self.gpt_4 = config["models"]["gpt4"]
        self.gpt_4o = config["models"]["gpt4o"]
        self.gpt_4o_mini = config["models"]["gpt4o_mini"]


class OpenAI:
    api_key: str

    def __init__(self):
        self.api_key = os.environ["OPENAI_API_KEY"]


class TMDB:
    access_token: str

    def __init__(self):
        self.access_token = os.environ["TMDB_ACCESS_TOKEN"]


class DiskCache:
    cache_dir: str

    def __init__(self, config: dict[str, any]):
        self.cache_dir = config["cache_dir"]

    @cached_property
    def web_cache(self):
        return Cache(self.cache_dir)

class GoogleSearch:
    google_api_key: str
    custom_search_engine_id: str

    def __init__(self, config: dict[str, any]):
        self.google_api_key = config["google_api_key"]
        self.custom_search_engine_id = config["custom_search_engine_id"]

    @cached_property
    def search_engine(self):
        return GoogleSearchAPIWrapper(google_api_key=self.google_api_key, google_cse_id=self.custom_search_engine_id)

class Shared:
    gpt: Optional[GPT] = None
    open_ai: Optional[OpenAI] = None
    tmdb: Optional[TMDB] = None
    disk_cache: Optional[DiskCache] = None
    google_search: Optional[GoogleSearch] = None
