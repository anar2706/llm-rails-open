import re
import os
import json
import requests
from langchain.schema import Document
from application.helpers.splitter import SpacyTextSplitter
from application.utils.create_embed import count_tokens
from application.utils.general import timefn

text_splitter = SpacyTextSplitter(
    chunk_size=2048,
    pipeline='en_core_web_lg',
    chunk_overlap=20
)

def parse_text(raw_text: str) -> list[str]:
    # Merge hyphenated words
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", raw_text)
    # Fix newlines in the middle of sentences
    text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
    # Remove multiple newlines
    text = re.sub(r"\n\s*\n", " ", text)
    return text


def text_to_docs(text, user, model, name = '', doc_type = '', url = ''):
    """Converts a string or list of strings to a list of Documents with metadata."""    
    page_docs = [Document(page_content=page) for page in text]
    
    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1

    doc_chunks = []
    for doc in page_docs:
        doc.page_content = parse_text(str(doc.page_content))
        chunk_size = 2048
    
        if model == 'embedding-multi-v1':
            chunk_size = 1024
            first_batch = str(doc.page_content)[:1000]
            token_count = count_tokens(first_batch, model)
            
            if token_count < 220 and chunk_size == 1024:
                chunk_size = 2048
        
        text_splitter._chunk_size = chunk_size
        chunks = text_splitter.split_text(str(doc.page_content))
        print(f'chunk_size {chunk_size} chunks {len(chunks)}')
        
        for index, chunk in enumerate(chunks):
            vec_doc = Document(page_content=chunk, metadata={"page":doc.metadata['page'],"chunk": index})            
            vec_doc.metadata["name"] = name
            vec_doc.metadata["type"] = doc_type
            vec_doc.metadata["url"]  = url

            doc_chunks.append(vec_doc)   
                         
                                            
    return doc_chunks


        