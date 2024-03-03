import os
import time
import json
from fastapi import Request
from application.utils.auth import check_auth
from fastapi import APIRouter, HTTPException
from application.models.semantic import SearchBody, SearchResponse
from models import Datastores, Usage, DatastoresDocuments, SearchLogs
from application.utils.retriever import WeaviateHybridSearchRetriever
from application.utils.semantic import summarize

router = APIRouter(prefix='/datastores/{datastore_id}')


@router.post('/search',tags=['Datastores'],name='Search')
def search_semantic(request: Request, datastore_id: str, arguments: SearchBody) -> SearchResponse:
	user_data = check_auth(request.headers)
		
	record = Datastores.select(Datastores.id,Datastores.vector_id, Datastores.embedding_model,Datastores.attributes).where(Datastores.pid==datastore_id,
		Datastores.workspace_id == user_data['workspace_id']).dicts()
	
	if not record:
		raise HTTPException(404, 'Datastore not found')

	documents = DatastoresDocuments.select().where(DatastoresDocuments.datastore_id == record[0]['id']).dicts()
	if not documents:
		raise HTTPException(400, 'To conduct a search, it is important to begin by adding relevant data.')
	
	attributes  = record[0]['attributes']
	search_resp = WeaviateHybridSearchRetriever(record[0]['vector_id'], record[0]['embedding_model'],
			user_data['key']).get_relevant_documents(arguments.text, arguments.hybrid, arguments.k, attributes, arguments.filters)
  
	resp = {'results':search_resp['docs']}
  
	if arguments.summarize:
		summarization = summarize(search_resp['docs'], arguments.text, user_data)
		resp['summarization'] = summarization['text']
	
	cdn_url = json.loads(os.environ['app'])['aws']['s3']
	for doc in search_resp['docs']:
		if doc.metadata['type'] in ['file','text']:
			doc.metadata['url'] = cdn_url + doc.metadata['url']
	
	subtype = 'platform' if user_data['is_internal'] else 'api'

	SearchLogs.create(type='search', text=arguments.text, user_id=user_data['user_id'], workspace_id=user_data['workspace_id'],
			datastore_id=record[0]['id'], created=time.time())

	Usage.create(type='datastore',subtype=subtype,unit='search',quantity=1,meta={"datastore_id": record[0]['id']},
        api_id=user_data['id'],workspace_id=user_data['workspace_id'],created=time.time())
	
	return resp
