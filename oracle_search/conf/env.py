import os
from enum import Enum
from functools import cached_property

import yaml

from typing import Optional, Type, TypeVar

T = TypeVar("T")


class _SingletonWrapper:
    _instance: Optional[T] = None

    def __init__(self, cls: Type):
        self._wrapped: Type = cls
        self._instance: Optional[T] = None

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = self._wrapped(*args, **kwargs)
        return self._instance


def singleton(cls: Type):
    return _SingletonWrapper(cls)


class Profile(str, Enum):
    DEV = "dev"
    PROD = "prod"

    @cached_property
    def is_dev(self) -> bool:
        return self == self.DEV

    @cached_property
    def is_production(self) -> bool:
        return self == self.PROD


@singleton
class Environment:
    def __init__(self):
        self.profile = Profile(os.getenv("EX_MACHINA_ENV", Profile.DEV.value))

        with open("config.yaml") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader).get(self.profile)
