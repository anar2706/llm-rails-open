import os
import json
import requests
from transformers import AutoTokenizer
from fastapi.exceptions import HTTPException
from application.utils.general import timefn


model_name = "intfloat/multilingual-e5-large"
multi_tokenizer = AutoTokenizer.from_pretrained(model_name)

model_name = "llmrails/ember-v1"
en_tokenizer = AutoTokenizer.from_pretrained(model_name)


def embed_text(input, model):
    url_mapping = json.loads(os.environ['app'])['embeddings']
    
    if model == 'embedding-english-v1':
        url = url_mapping['english']
    else:
        url = url_mapping['multi']

    vector_resp = requests.post(url + '/embed',json={
        'inputs':input,
        'truncate':True
    })

    payload = vector_resp.json()

    if isinstance(payload, dict) and payload.get('error'):
        raise HTTPException(400, payload['error'])
    
    return payload


@timefn
def create_embedding(input, model):
    if isinstance(input, str):
        input = [input]

    if len(input) > 10:
        raise HTTPException(400,'User input can not contain more that 10 items')

    response = []
    
    if model == 'embedding-english-v1':
        texts = [t.replace("\n", " ") for t in input]
        token_count = count_tokens(' '.join(texts), model)
    
    else:
        texts = [t.replace("\n", " ") for t in input]
        token_count = count_tokens(' '.join(texts), model)
    
    payload = embed_text(input, model)
    
    for index, embedding in enumerate(payload):
        
        if embedding[0] == None:
            print(input[index])
            embedding = embed_text(input[index], model)[0]

        response.append(
            {
                "object": "embedding",
                "index": index,
                "embedding":embedding
            }
        )

    return response, token_count


def count_tokens(text, model):
    tokenizer = multi_tokenizer
    
    if model == 'embedding-english-v1':
        tokenizer = en_tokenizer
    
    encoded = tokenizer.encode(text)
    return len(encoded)
    

    