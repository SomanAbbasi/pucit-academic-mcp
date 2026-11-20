
import streamlit as st

from langchain.messages import HumanMessage

from agent.agent import agent


st.set_page_config(
    page_title="PUCIT GPA Assistant",
    page_icon=None,
    layout="centered",
)


st.title("PUCIT GPA & CGPA Assistant")

st.caption("Ask questions about GPA, CGPA, courses, and credit hours.")


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    if message.type == "human":
        with st.chat_message("user"):
            st.write(message.content)

    elif message.type == "ai":
        with st.chat_message("assistant"):
            st.write(message.text)


user_input = st.chat_input("Ask about your GPA or CGPA...")


if user_input:
    st.session_state.messages.append(
        HumanMessage(content=user_input)
    )

    with st.chat_message("user"):
        st.write(user_input)

    result = agent.invoke({
        "messages": st.session_state.messages
    })

    st.session_state.messages = result["messages"]

    with st.chat_message("assistant"):
        st.write(st.session_state.messages[-1].text)