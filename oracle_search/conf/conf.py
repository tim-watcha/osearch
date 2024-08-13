import os
from functools import cached_property
from typing import Optional

from diskcache import Cache


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

class Shared:
    gpt: Optional[GPT] = None
    open_ai: Optional[OpenAI] = None
    tmdb: Optional[TMDB] = None
    disk_cache: Optional[DiskCache] = None
