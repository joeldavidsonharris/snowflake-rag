-- Original guide: https://quickstarts.snowflake.com/guide/ask_questions_to_your_own_documents_with_snowflake_cortex_search/#0

------------------ 1. Account Setup ------------------

use role accountadmin;

drop warehouse compute_wh;
drop database snowflake_sample_data;

alter account set
timezone = 'Pacific/Auckland'
week_start = 1
timestamp_type_mapping = timestamp_ltz
enable_unredacted_query_syntax_error = true
cortex_enabled_cross_region = 'ANY_REGION';

use role sysadmin;

create warehouse rag_wh
warehouse_size = xsmall
auto_suspend = 60
initially_suspended = true;

create database rag;

drop schema rag.public;

use role securityadmin;

grant imported privileges on database snowflake to role sysadmin;

use role sysadmin;
use warehouse rag_wh;
use database rag;

create schema rag.poc;

------------------ 2. Loading Data ------------------

use role sysadmin;
use warehouse rag_wh;
use schema rag.poc;

create or replace function text_chunker(pdf_text string)
returns table (chunk varchar)
language python
runtime_version = '3.11'
handler = 'text_chunker'
packages = ('snowflake-snowpark-python', 'langchain')
as
$$
# Imports
from snowflake.snowpark.types import StringType, StructField, StructType
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

class text_chunker:
    def process(self, pdf_text: str):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,  # adjust this as you see fit
            chunk_overlap=256,  # allows some overlap for context retention
            length_function=len
        )
        
        chunks = text_splitter.split_text(pdf_text)
        df = pd.DataFrame(chunks, columns=['chunks'])
        
        yield from df.itertuples(index=False, name=None)
$$;

create or replace stage docs
encryption = (type = 'snowflake_sse') 
directory = (enable = true);

-- ALTER: Change the file path to match your files
put 'file:///home/joel/projects/snowflake-rag/sky-tv-annual-report-2024-pages-1-to-50.pdf' @docs auto_compress=false overwrite=true;
put 'file:///home/joel/projects/snowflake-rag/sky-tv-annual-report-2024-pages-51-to-100.pdf' @docs auto_compress=false overwrite=true;
put 'file:///home/joel/projects/snowflake-rag/sky-tv-annual-report-2024-pages-101-to-132.pdf' @docs auto_compress=false overwrite=true;

ls @docs;

alter stage docs refresh;

------------------ 3. Data Preperation ------------------

create or replace table docs_chunks ( 
    relative_path varchar, -- relative path to the pdf file
    size number, -- size of the pdf
    file_url varchar, -- url for the pdf
    scoped_file_url varchar, -- scoped url (choose which one to keep based on use case)
    chunk varchar -- piece of text
);

insert overwrite into docs_chunks (relative_path, size, file_url, scoped_file_url, chunk)
select 
    relative_path,
    size,
    file_url,
    build_scoped_file_url(@docs, relative_path) as scoped_file_url,
    func.chunk as chunk
from directory(@docs),
    table(text_chunker(to_varchar(snowflake.cortex.parse_document(@docs, relative_path, {'mode': 'LAYOUT'})))) as func;

------------------ 4. Search Service ------------------

create or replace cortex search service vector_store
on chunk
warehouse = rag_wh
target_lag = '1 minute'
as (
    select 
        chunk,
        relative_path,
        file_url
    from docs_chunks
);

------------------ 5. Streamlit App ------------------

create or replace stage code
encryption = (type = 'snowflake_sse')
directory = (enable = true);

-- ALTER: Change the file path to match your filepath
put 'file:///home/joel/projects/snowflake-rag/rag-app.py' @code auto_compress=false overwrite=true;
put 'file:///home/joel/projects/snowflake-rag/environment.yml' @code auto_compress=false overwrite=true;

ls @code;

create or replace streamlit chatbot
root_location = '@rag.poc.code'
main_file = 'rag-app.py'
query_warehouse = rag_wh;
