import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from Retriever import retriever
from LLM import LLM, llm
import logging


def handleClearMessages():
    try:
        st.session_state.messages = []
        st.success(f"Successfully cleared messages.")
    except Exception as e:
        st.error(f"Unable to clear messages.")


lcol, rcol = st.columns([0.8, 0.2], vertical_alignment="center")
lcol.title("Chat with Documents")
rcol.button("Clear Messages", on_click=handleClearMessages, use_container_width=True)

if not retriever.compression_retriever:
    st.error(f"There is no retriever created yet.")
else:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if query_text := st.chat_input("What is your query?"):
        st.session_state.messages.append({"role": "user", "content": query_text})
        with st.chat_message("user"):
            st.markdown(query_text)

        with st.chat_message("assistant"):
            retrieved_docs = retriever.invoke_with_score_filter(query=query_text)
            prompt = LLM.construct_prompt(retrieved_docs, query_text)
            logging.info(f"retrieved_docs: {retrieved_docs}")
            logging.info(f"prompt: {prompt}")

            thinking_expander = st.expander("Thinking...", expanded=True)
            thinking_placeholder = thinking_expander.empty()
            message_placeholder = st.empty()
            response_content = ""
            thinking_content = ""
            in_thinking = False
            full_response = None

            for chunk in llm.model.stream(prompt):
                chunk_content = chunk.content
                if "<think>" in chunk_content:
                    in_thinking = True
                    thinking_content += chunk_content.replace("<think>", "")
                    thinking_placeholder.markdown(thinking_content)
                    continue
                elif "</think>" in chunk_content:
                    in_thinking = False
                    thinking_content += chunk_content.replace("</think>", "")
                    thinking_placeholder.markdown(thinking_content)
                    continue
                elif in_thinking:
                    thinking_content += chunk_content
                    thinking_placeholder.markdown(thinking_content)
                    continue

                response_content += chunk_content
                message_placeholder.markdown(response_content + "▌")
                full_response = chunk if full_response is None else full_response + chunk

            message_placeholder.markdown(response_content)

            # Clear the thinking placeholder if no thinking content was added
            if not thinking_content:
                thinking_placeholder.empty()

            formatted_refs = [
                f"Score: {doc.metadata.get('relevance_score', None):.4f} \tSource: {doc.metadata.get('source', None)} \tPage number: {int(doc.metadata.get('page')) + 1}"
                for doc in retrieved_docs
            ]
            formatted_refs = "\n\n**Sources:**\n" + "\n".join([f"- {ref}" for ref in formatted_refs])

            with st.expander(f"Document reference:"):
                st.markdown(formatted_refs)

            if full_response.usage_metadata:
                with st.expander("**Usage Metadata:**"):
                    st.json(full_response.usage_metadata)

            logging.info(f"sources: {formatted_refs}")
            logging.info(f"Usage_metadata: {full_response.usage_metadata}")

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_content
                + formatted_refs
                + (f"\n**Usage Metadata:** {full_response.usage_metadata}" if full_response.usage_metadata else ""),
            }
        )
