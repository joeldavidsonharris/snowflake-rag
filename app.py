# Imports
from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import streamlit as st
import pandas as pd
import json

pd.set_option("max_colwidth", None)

# Search constants
CORTEX_SEARCH_DATABASE = "RAG"
CORTEX_SEARCH_SCHEMA = "POC"
CORTEX_SEARCH_SERVICE = "VECTOR_STORE"
NUM_CHUNKS = 10  # Number of chunks to include in RAG context
COLUMNS = ["chunk", "relative_path"]
CHAT_MODEL = "mixtral-8x7b"

# Create clients
session = get_active_session()
root = Root(session)
svc = (
    root.databases[CORTEX_SEARCH_DATABASE]
    .schemas[CORTEX_SEARCH_SCHEMA]
    .cortex_search_services[CORTEX_SEARCH_SERVICE]
)


def config_options():
    st.sidebar.write(
        "Documents to be used:"
    )
    docs_available = session.sql("ls @docs").collect()
    list_docs = []
    for doc in docs_available:
        list_docs.append(doc["name"].split("/")[-1])
    st.sidebar.dataframe(list_docs, column_config={"value": "Documents"})


def get_similar_chunks_search_service(query):
    response = svc.search(query, COLUMNS, limit=NUM_CHUNKS)
    st.sidebar.json(response.json())
    return response.json()


def create_prompt(question):
    prompt_context = get_similar_chunks_search_service(question)

    prompt = f"""
        You are an expert chat assistance that extracts information from the CONTEXT provided
        between <context> and </context> tags.
        When answering the question contained between <question> and </question> tags
        be concise and do not hallucinate.
        Only output information that you see in your CONTEXT, do not make anything up.
        If you don't have the information just say so.
        Only answer the question if you can extract it from the CONTEXT provided.
        Provide your output in markdown format.

        Do not reference the CONTEXT used in your answer.
        Don't say things like "Based on the provided context".

        <context>          
        {prompt_context}
        </context>
        <question>  
        {question}
        </question>
        Answer: 
    """

    json_data = json.loads(prompt_context)

    relative_paths = set(item["relative_path"] for item in json_data["results"])

    return prompt, relative_paths


def complete(question):
    prompt, relative_paths = create_prompt(question)
    sql_command = "select snowflake.cortex.complete(?, ?) as response"

    df_response = session.sql(
        sql_command, params=[CHAT_MODEL, prompt]
    ).collect()

    return df_response[0].RESPONSE.replace('$', '\$'), relative_paths


def main():
    st.title("Documentation Assistant")

    config_options()

    question = st.text_input(
        "Ask the documentation a question",
        placeholder="Ask your question here",
        label_visibility="collapsed",
    )

    if question:
        response, relative_paths = complete(question)
        st.write(response)

        if relative_paths != "None":
            with st.sidebar.expander("Related Documents"):
                for path in relative_paths:
                    sql_command = f"select get_presigned_url(@docs, '{path}', 360) as url_link from directory(@docs)"
                    df_url_link = session.sql(sql_command).to_pandas()
                    url_link = df_url_link._get_value(0, "URL_LINK")

                    display_url = f"Doc: [{path}]({url_link})"
                    st.sidebar.markdown(display_url)


if __name__ == "__main__":
    main()
