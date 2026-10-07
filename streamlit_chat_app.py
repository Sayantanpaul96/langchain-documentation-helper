#!/usr/bin/env python3
"""
Streamlit chat application for the langchain documentation helper.
This application allows users to chat with the RAG system through a web interface.
Running it is as simple as streamlit run streamlit_chat_app.py
"""

import streamlit as st
import sys
import os

# Add the backend directory to the path so we can import from core.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from core import run_llm

def main():
    """
    Main Streamlit application for the chat interface.
    """
    # Page configuration
    st.set_page_config(
        page_title="Langchain Documentation Helper",
        page_icon="🦜",
        layout="centered"
    )

    # Header
    st.title("🦜 Langchain Documentation Helper")
    st.caption("Ask questions about Langchain documentation and get AI-powered answers")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask a question about Langchain documentation..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching documentation..."):
                try:
                    # Call the RAG pipeline from core.py
                    result = run_llm(prompt)
                    answer = result['answer']

                    # Display the answer
                    st.markdown(answer)

                    # Optionally show retrieved sources in an expander
                    if result['context']:
                        with st.expander("📚 View Sources"):
                            for i, doc in enumerate(result['context'], 1):
                                source = doc.metadata.get('source', 'Unknown')
                                st.markdown(f"**Source {i}:** {source}")
                                st.markdown(f"*Content preview:* {doc.page_content[:200]}...")
                                st.divider()

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    answer = f"Sorry, I encountered an error: {str(e)}"

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()