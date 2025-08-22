# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Adapted from https://github.com/kyopark2014/strands-agent
# SPDX-License-Identifier: MIT

import logging
import sys

import streamlit as st

import health_agent_async

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("streamlit")

# title
st.set_page_config(
    page_title="Clinical Decision Support AI Assistant",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

with st.sidebar:
    st.title("Clinical Assistant Menu")

    st.markdown(
        "**Clinical Decision Support AI Assistant** with access to patient data through MCP healthcare server. "
        "This assistant helps healthcare professionals with diagnostic reasoning and clinical decision-making. "
    )

    
    # Healthcare-specific information
    st.markdown("### Available Patient Data")
    st.markdown("""
    **Sample Patient IDs:**
    - PAT001, PAT002, PAT003
    
    **Available Tools:**
    - Patient Demographics
    - Medical History
    - Lab Results
    - Patient Search
    - Risk Assessment
    """)
    
    st.markdown("---")
    
    st.markdown("### ⚠️ Important Notice")
    st.markdown("""
    This is a **clinical decision support tool** for healthcare professionals only. 
    
    - Not a replacement for clinical judgment
    - Final decisions must be made by qualified healthcare professionals
    - Maintains HIPAA compliance principles
    """)

    clear_button = st.button("Reset Conversation", key="clear")

st.title("🏥 Clinical Decision Support AI Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greetings = False

# Display chat messages from history on app rerun
def display_chat_messages():
    """Print message history
    @returns None
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "images" in message:
                for url in message["images"]:
                    logger.info(f"url: {url}")
                    file_name = url[url.rfind("/") + 1 :]
                    st.image(url, caption=file_name, use_container_width=True)
            st.markdown(message["content"])

display_chat_messages()

# Greet user
if not st.session_state.greetings:
    with st.chat_message("assistant"):
        intro = """👋 Welcome to the Clinical Decision Support AI Assistant!

I'm here to help healthcare professionals with:
- **Diagnostic reasoning** and differential diagnoses
- **Patient data analysis** using our MCP healthcare server
- **Clinical insights** based on medical guidelines
- **Treatment recommendations** considering patient history
- **Lab result interpretation** and clinical findings

I have access to patient data for sample patients (PAT001, PAT002, PAT003) and can help with clinical decision-making.

**Important:** I'm a support tool for healthcare professionals, not a replacement for clinical judgment. All recommendations are for clinical decision support only.

How can I assist you with your clinical analysis today?"""
        
        st.markdown(intro)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": intro})
        st.session_state.greetings = True

if clear_button or "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greetings = False
    st.rerun()

# Always show the chat input
if prompt := st.chat_input("Enter your clinical question or patient case..."):
    with st.chat_message("user"):  # display user message in chat message container
        st.markdown(prompt)

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )  # add user message to chat history
    prompt = prompt.replace('"', "").replace("'", "")
    logger.info(f"Clinical prompt: {prompt}")

    with st.chat_message("assistant"):
        response = health_agent_async.run_health_agent(prompt, st)

    st.session_state.messages.append({"role": "assistant", "content": response})
