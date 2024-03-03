import os
import json
import numpy as np
import requests
from uuid import uuid4
from fastapi.exceptions import HTTPException
from application.helpers.connections import w_client
from weaviate.util import get_valid_uuid
from application.models.semantic import Document
from application.helpers.connections import MODELS
from application.helpers.core import send_log_slack_message
from application.helpers.constants import operator_mapping, value_types
from application.router.embed import embed_internal
from application.utils.general import timefn

class WeaviateHybridSearchRetriever:
    def __init__(self, index_name, model, api_key):
        
        self.alpha = 0.5
        self.index = index_name
        self.model = model
        self.api_key  = api_key
        self.embedding_api = json.loads(os.environ['app'])['embedding_api']
        
        if self.model not in MODELS:
            raise HTTPException(400,f'The model `{self.model}` does not exist')
        
    def get_vector(self, chunks):
        vectors = embed_internal(chunks, self.model, {'x-api-key':self.api_key})
        return vectors['data'], vectors['usage']['prompt_tokens']

    
    @timefn
    def add_documents(self, docs, doc_id, attributes, metadata={}):
        """Upload documents to Weaviate."""

        tokens = 0
        w_client.batch.configure(batch_size=50)
        attributes = {i['name']: i['type'] for i in attributes}
        
        with w_client.batch as batch:
            ids = []
            
            for i in range(0, len(docs), 10):
                part_chunks = [item for item in docs[i: i+10]]
                vectors, token_count = self.get_vector([item.page_content for item in part_chunks])
                tokens += token_count
                
                for vector in vectors:
                    index = vector['index']
                    document = part_chunks[index]
                    
                    data_properties = {
                        "text": document.page_content,
                        "type": document.metadata["type"],
                        "url": document.metadata["url"],
                        "name": document.metadata["name"],
                        "doc_id": doc_id
                    }

                    for key, value in metadata.items():
                        field_type = attributes.get(key)
                        if not field_type:
                            continue

                        if field_type == 'text':
                            value = str(value)

                        elif field_type == 'number':
                            value = float(value)

                        else:
                            value = int(value)

                        data_properties[key] = value

                    _id = get_valid_uuid(uuid4())
                    batch.add_data_object(data_properties, self.index, _id, vector=vector['embedding'])
                    ids.append(_id)
                    
                print(f'i {i}')
             
        return tokens

    def get_relevant_documents(self, query: str, hybrid=True, k=5, attributes=None, filters=None):
        """Look up similar documents in Weaviate."""
        vector_resp = self.get_vector([query])

        fields = ['text','type','name','url']
        meta_fields = []
        
        if attributes:
            meta_fields = [i['name'] for i in attributes]
            fields += meta_fields

        resp = w_client.query.get(self.index, fields)
        if hybrid:
            resp = resp.with_hybrid(query=query, alpha=self.alpha, vector=vector_resp[0][0]['embedding'])
        
        else:
            resp = resp.with_near_vector({"vector":vector_resp[0][0]['embedding']})

        if filters:
            condition = {
                'operator': filters.operator.capitalize(),
                'operands':[]
            }

            for operand in filters.conditions:
                op_type = [i['type'] for i in attributes if i['name'] == operand.field][0]

                condition['operands'].append({
                    'path': [operand.field],
                    'operator': operator_mapping[operand.operator],
                    value_types[op_type]: operand.value
                })
            
            print(json.dumps(condition, indent=4))
            resp = resp.with_where(condition)
        
        response = resp.with_additional(["score", "explainScore","distance","vector"]).with_limit(k).do()

        if response.get('errors'):
            print(response['errors'])
            send_log_slack_message(f"Semantic Search Error {response['errors']}")
            raise HTTPException(500, 'Error happened on semantic search')
            
            
        docs = []
        for res in response["data"]["Get"][self.index]:
            if hybrid:
                real_score = 1 - 1 / (1 + np.exp(float(res["_additional"]["score"])))
                
            else:
                real_score = np.dot(res["_additional"]["vector"], vector_resp[0][0]['embedding'])
            
            res['_additional'].pop('vector',None)
            
            metadata = {
                "type": res["type"],
                "name": res["name"],
                "url": res["url"],
                "score":real_score,
                "filters":{},
                "explain_score":res["_additional"]["explainScore"]
            }

            for meta_field in meta_fields:
                metadata['filters'][meta_field] = res[meta_field]
        
            docs.append(Document(text=res["text"], metadata=metadata))

        return {'docs':docs,'tokens':vector_resp[1]}
