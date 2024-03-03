import time
import random
from project.celery import app
from application.utils.general import num_tokens_from_messages
from application.utils.handler import DataHandler
from application.utils.retriever import WeaviateHybridSearchRetriever
from application.utils.upload import upload_text_file
from models import DatastoresDocuments, Usage, ChatMessages, EmbeddingsLogs


@app.task(name='semantic.upload_file_vector',acks_late=True,soft_time_limit=1800)
def upload_file_vector(**kwargs):
    file   = kwargs['file'] 
    user   = kwargs['user']
    dstore = kwargs['datastore']
    document_id = kwargs['document_id']
    
    try:
        docs  = DataHandler.load_file(file, dstore['embedding_model'],user)
        token_count = WeaviateHybridSearchRetriever(dstore['vector_id'], dstore['embedding_model'], 
            user['key']).add_documents(docs, document_id, dstore['attributes'], kwargs['metadata'])
        
    except Exception as e:
        DatastoresDocuments.update(status=3, 
            meta={'error':'Error happened while embedding file'}).where(DatastoresDocuments.id==document_id).execute()
        raise e
    
    DatastoresDocuments.update(status=1, 
            tokens=token_count).where(DatastoresDocuments.id==document_id).execute()
      
      
@app.task(name='semantic.upload_text_vector',acks_late=True,soft_time_limit=1800)
def upload_text_vector(**kwargs): 
    user   = kwargs['user']
    dstore = kwargs['datastore']
    document_id = kwargs['document_id']
    
    try:
        url = upload_text_file(kwargs['text'],kwargs['name'],dstore['pid'])
        docs = DataHandler.load_text(kwargs['text'], dstore['embedding_model'], user,
            kwargs['name'], dstore['pid'], url)
        
        token_count = WeaviateHybridSearchRetriever(dstore['vector_id'], dstore['embedding_model'], 
                user['key']).add_documents(docs, document_id, dstore['attributes'], kwargs['metadata'])
        
    except Exception as e:
        DatastoresDocuments.update(status=3, 
            meta={'error':'Error happened while embedding text'}).where(DatastoresDocuments.id==document_id).execute()
        raise e
    
    DatastoresDocuments.update(status=1,tokens=token_count,bytes=len(kwargs['text'].encode('utf-8'))).where(DatastoresDocuments.id==document_id).execute()
 
 
@app.task(name='semantic.upload_website_vector',acks_late=True,soft_time_limit=600)
def upload_website_vector(user, datastore, link, doc_id):  
    try:
        docs, size = DataHandler.load_website(link,datastore['id'],user,datastore['embedding_model'])
        tokens = WeaviateHybridSearchRetriever(datastore['vector_id'], datastore['embedding_model'],
                user['key']).add_documents(docs, doc_id, datastore['attributes'])
    
    except Exception as e:
        DatastoresDocuments.update(status=3, 
            meta={'error':'Error happened while embedding website'}).where(DatastoresDocuments.id==doc_id).execute()
        raise e
    
    DatastoresDocuments.update(status=1, tokens=tokens,bytes=size).where(DatastoresDocuments.id==doc_id).execute()
 
 
@app.task(name='semantic.upload_websites',acks_late=True,soft_time_limit=1800,task_serializer='json')
def upload_websites(**kwargs):
    user    = kwargs['user']
    dstore  = kwargs['datastore']  
    records = kwargs['records']
    print(len(records))

    for record in records:
        upload_website_vector.delay(user, dstore, record['meta']['task_id'], record['id'])
        
        
@app.task(name='semantic.openai_usage',acks_late=True,soft_time_limit=60,task_serializer='json')
def openai_usage(**kwargs):  
    user     = kwargs['user']
    model    = kwargs['model']
    processs = kwargs['process']
    msg_pid   = kwargs['msg_id']
    
    message_record = ChatMessages.select(ChatMessages.id).where(ChatMessages.pid==msg_pid).dicts()
    if message_record:
        message_id = message_record[0]['id']

    else:
        message_id = 0
    
    if processs:
        input  = num_tokens_from_messages(kwargs['input'],model)
        output = num_tokens_from_messages(kwargs['output'],model)
        
    else:
        input = kwargs['input']
        output = kwargs['output']
        
    Usage.create(type='chat-app',subtype=model,unit='tokens',quantity=input+output,
        meta={'input':input,'output':output,'message_id':message_id},api_id=user['id'],
        workspace_id=user['workspace_id'],created=time.time()
    )

      
@app.task(name='semantic.embedding_usage',acks_late=True,soft_time_limit=60,task_serializer='json')
def embedding_usage(**kwargs):  
    user     = kwargs['user']
    model    = kwargs['model']
    token    = kwargs['token']
    text     = kwargs['text']
    internal_api = kwargs.get('internal_api')

    
    if user['is_internal']:
        Usage.create(type='embedding-internal',subtype=model,unit='tokens',quantity=token,
            api_id=user['id'],workspace_id=user['workspace_id'],created=time.time())
    
    elif internal_api:
        Usage.create(type='embedding-internal',subtype=model,unit='tokens',quantity=token,
            api_id=user['id'],workspace_id=user['workspace_id'],created=time.time())
    
    else:
        Usage.create(type='embedding',subtype=model,unit='tokens',quantity=token,
            api_id=user['id'],workspace_id=user['workspace_id'],created=time.time())
    
    EmbeddingsLogs.create(user_id=user['user_id'], workspace_id=user['workspace_id'],model=model,
        text={'text':text}, created=time.time())
    
    