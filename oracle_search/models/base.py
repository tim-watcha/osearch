from typing import List

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    language: str = Field(description="Language of the query.")
    query: str = Field(description="Search query generated based on the refined request.")
    recent_days: int = Field(title="The number of days to search for the query. Default is -1 (no limit).")


class GeneratedQuery(BaseModel):
    queries: List[SearchQuery] = Field(description="List of search queries generated based on the refined request.")


class RedefinedRequest(BaseModel):
    ambiguity: List[str] = Field(
        description="Describe the ambiguity in the original request, including terms and title..")
    background_information: List[str] = Field(
        description="Organize any background information that related to the request.")
    redefined_request: str = Field(
        description="Redefined request derived from the Request. Keeping original purpose, focus on avoiding ambiguity, while. Redefined request should be self-contained and clear. Should be in Korean")
