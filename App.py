import streamlit as st
import asyncio
from aiohttp import ClientSession
from oracle_search.web_loader.web_loader import WebContentExtractor
from oracle_search import ExMachina

# Bootstrap the application
ExMachina.bootstrap()

async def fetch_url_content(url: str, request: str):
    async with ClientSession() as session:
        extractor = WebContentExtractor(url, session)
        content = await extractor.afetch()
        return content, request

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
    if submit_button and url and request:
        st.success("Submitted!")
        
        content, request = asyncio.run(fetch_url_content(url, request))
        
        if isinstance(content, (str, dict)):
            st.session_state.content = str(content)
        elif hasattr(content, 'page_content'):
            st.session_state.content = content.page_content
        else:
            st.error("Unable to fetch the content.")
            st.session_state.content = None
        
        st.session_state.request = request

        # Display URL, Request, and fetched content in a folded box
        with st.expander("View URL, Request, and Fetched Content", expanded=False):
            st.write(f"Fetched content from: {url}")
            st.write(f"Request: {request}")
            if st.session_state.content:
                st.text_area("Fetched Content:", value=st.session_state.content[:500] + "...", height=200)

    # Chat interface (only shown after content is fetched)
    if st.session_state.content and st.session_state.request:
        st.subheader("Chat about the fetched content")

        # Display chat messages from history
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
