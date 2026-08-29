import streamlit as st
from graph.build_graph import graph

st.set_page_config(
    page_title="CRM Agent",
    page_icon="🤖"
)

st.title("CRM Multi-Agent Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask a CRM question..."):

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking...."):

            final_result = {}

            for event in graph.stream({
                "question": question,
                "route": None,
                "sql_result": None,
                "rag_result": None,
                "answer": None,
            }):
                print("EVENT:", event)
                for node_name, node_result in event.items():
                    if isinstance(node_result, dict):
                        final_result.update(node_result)

            answer = (
                final_result.get("answer")
                or final_result.get("sql_result")
                or final_result.get("rag_result")
                or "No answer found."
            )

            route = final_result.get("route", "unknown")

            st.markdown(answer)
            st.caption(f"Route: {route}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })