# Snowflake RAG Chatbot Demo

This repository contains a demo of an Snowflake-based AI chatbot that can answer questions about information in a set of PDF files.

## Prerequisites

- Python 3.11
- Snowflake account
- VSCode with the Snowflake extension configured

## Setup
### Clone the repository

```bash
git clone https://github.com/joeldavidsonharris/snowflake-rag
cd snowflake-rag
```

### Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install pypdf2
```

### Prepare the PDF files

This step is only needed if your PDF files are larger than 100 pages.

```bash	
python prepare_files.py <file 1> <file 2> --chunk_size <n>
```

Using the example sky-tv-annual-report-2024.pdf file:
```bash
python prepare_files.py sky-tv-annual-report-2024.pdf --chunk_size 50
```

The output using the example file will be:
```
sky-tv-annual-report-2024-pages-1-to-50.pdf
sky-tv-annual-report-2024-pages-51-to-100.pdf
sky-tv-annual-report-2024-pages-101-to-132.pdf
```

### Update SQL script

Update the `rag.sql` script to reference your PDF files. If you split your PDF files, you will need to reference the split versions.

Areas to update are denoted by `ALTER` comments.

### Create Snowflake resources

Run `rag.sql` against your Snowflake account, using the VSCode Snowflake extension

### Talk to the chatbot

Open the `CHATBOT` Streamlit application in the Snowflake UI and ask questions about the content of your PDF files

