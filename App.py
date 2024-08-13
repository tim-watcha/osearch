import streamlit as st
import asyncio
from aiohttp import ClientSession
from oracle_search.web_loader.web_loader import WebContentExtractor
from oracle_search.config import Config
from oracle_search.shared import Shared

# Initialize configuration and shared resources
config = Config()
Shared.init(config)

async def fetch_url_content(url: str):
    async with ClientSession() as session:
        extractor = WebContentExtractor(url, session)
        content = await extractor.afetch()
        return content

def main():
    st.set_page_config(page_title="URL Content Fetcher", layout="wide")
    st.title("URL Content Fetcher")

    # Create a form
    with st.form(key='url_form'):
        # Add a text input for the URL
        url = st.text_input(label="Enter URL")

        # Add a submit button
        submit_button = st.form_submit_button(label="Submit")

    # Check if the form is submitted
    if submit_button and url:
        st.success("Submitted!")
        st.write(f"Fetching content from: {url}")
        
        # Fetch and display the content
        content = asyncio.run(fetch_url_content(url))
        
        if isinstance(content, (str, dict)):
            st.json(content)
        elif hasattr(content, 'page_content'):
            st.text_area("Fetched Content:", value=content.page_content, height=300)
            st.json(content.metadata)
        else:
            st.error("Unable to display the fetched content.")

if __name__ == "__main__":
    main()
