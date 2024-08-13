from oracle_search.conf.conf import GPT, Shared, OpenAI, TMDB, DiskCache
from oracle_search.conf.env import Environment


class ExMachina:
    @classmethod
    def bootstrap(cls):
        config = Environment().config

        Shared.gpt = GPT(config["gpt"])
        Shared.open_ai = OpenAI()
        Shared.tmdb = TMDB()
        Shared.disk_cache = DiskCache(config["disk_cache"])
