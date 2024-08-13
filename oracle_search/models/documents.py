from typing import Literal, Dict, Union

from pydantic import BaseModel


class WebContent(BaseModel):
    page_content: str
    source: str
    metadata: Dict[Literal["title", "description", "keywords", "published_date", "source", "summary"], Union[str, None]]


class YoutubeTranscript(BaseModel):
    page_content: str
    source: str
    metadata: Dict[
        Literal["title", "description", "keywords", "channel_name", "published_date", "source", "summary"],
        Union[str, None],
    ]
