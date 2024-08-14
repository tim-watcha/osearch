import asyncio
from typing import Union

import streamlit as st
from aiohttp import ClientSession

from oracle_search import ExMachina
from oracle_search.chain.base import get_refined_request, get_search_query
from oracle_search.models.documents import WebContent, YoutubeTranscript
from oracle_search.tools.web_tools import answer_with_contents
from oracle_search.web_loader.search import aget_search_full_contents
from oracle_search.web_loader.web_loader import WebContentExtractor

# Bootstrap the application
ExMachina.bootstrap()


async def fetch_url_content(url: str) -> Union[WebContent, YoutubeTranscript]:
    async with ClientSession() as session:
        extractor = WebContentExtractor(url, session)
        content = await extractor.afetch()
        return content


def get_bot_response(user_input, content, request):
    # For now, the bot just responds with the fetched content and request
    return f"Based on the request '{request}' and the fetched content, here's a response: {content[:200]}..."


def main():
    st.set_page_config(page_title="URL Content Fetcher and Chat", layout="wide")
    st.title("URL Content Fetcher and Chat")

    # Initialize session state
    if "content" not in st.session_state:
        st.session_state.content = None
    if "request" not in st.session_state:
        st.session_state.request = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # URL and Request submission form
    with st.form(key='url_form'):
        url = st.text_input(label="Enter URL")
        request = st.text_area(label="Enter your request")
        submit_button = st.form_submit_button(label="Submit")

    # Fetch content when URL and Request are submitted
    if submit_button and request:
        st.success("Submitted!")
        if url:
            content = asyncio.run(fetch_url_content(url))
            st.session_state.content = content
            st.session_state.request = get_refined_request(content, request).redefined_request

            # Display URL, Request, and fetched content in a folded box
            with st.expander("View URL, Request, and Fetched Content", expanded=False):
                st.write(f"Fetched content from: {url}")
                if st.session_state.content:
                    st.text_area("Fetched Content:", value=st.session_state.content, height=200)
        else:
            st.session_state.request = request

    # Chat interface (only shown after content is fetched)
    if st.session_state.request:
        st.write(st.session_state.request)
        queries = get_search_query(st.session_state.request)
        st.write(queries)
        search_results = asyncio.run(aget_search_full_contents(queries.queries))

        st.write(answer_with_contents(search_results, st.session_state.request))

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Ask about the content"):
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get and display bot response
            response = get_bot_response(prompt, st.session_state.content, st.session_state.request)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
