import time
import uuid
import validators
from fastapi import Request
from peewee import chunked
from project.celery import parser_app
from fastapi import APIRouter,HTTPException
from application.utils.auth import check_auth
from models import Datastores, DatastoresDocuments, db
from project.celery import app as c_app
from crawl_models import CrawlerSites, CrawlerTasks
from application.models.crawler import (CrawlTaskRequest, CrawlTaskResponse, 
        CrawlStatusResponse, VectorizeResponse, VectorizeRequest)


router = APIRouter()


@router.post('/datastores/website',name='Start Crawl Task',tags=['Crawl'])
def crawl_website(arguments: CrawlTaskRequest, request: Request) -> CrawlTaskResponse:
    check_auth(request.headers)
    print(arguments.dict())

    url_validated = validators.url(arguments.link)
    if not url_validated:
        raise HTTPException(400, 'Url is not valid')

    
    task_id = f"crw_{uuid.uuid4()}"
    parser_app.send_task(
        "test.test",
        kwargs={
            "id": task_id,
            "one_page":arguments.one_page,
            "url": arguments.link,
        },queue="crawler",
    )
    
    return {'id':str(task_id)}



@router.get('/datastores/website/{task_id}',tags=['Crawl'],name='Get Crawl results')
def get_crawl_status(task_id: str, request: Request) -> CrawlStatusResponse:
    check_auth(request.headers)
    
    site_data = CrawlerSites.select().where(CrawlerSites.task_id==task_id).dicts()
    if not site_data:
        raise HTTPException(400, 'Website Task not found')
    
    site_data = site_data[0]
    status = site_data['status']
    response = {'status':'processing' if status == 0 else 'completed', 'total':site_data['total'], 'links':[]}
    
    if status == 1:
        links = CrawlerTasks.select(CrawlerTasks.id, CrawlerTasks.url).where(CrawlerTasks.task_id == task_id,
                CrawlerTasks.status < 299).dicts()
        
        response['links'] = list(links)
        
    return response


@router.post('/datastores/{datastore_id}/website/{task_id}/embed',description='Embed websites',tags=['Crawl'])
def vectorize_website(datastore_id: str, task_id: str, arguments: VectorizeRequest, request: Request) -> VectorizeResponse:
    user_data = check_auth(request.headers)
    
    record = Datastores.select(Datastores.id, Datastores.vector_id,Datastores.embedding_model,
            Datastores.attributes).where(Datastores.pid==datastore_id, Datastores.workspace_id == user_data['workspace_id']).dicts()
    
    if not record:
        raise HTTPException(404, 'Datastore not found')
    
    site_data = CrawlerSites.select().where(CrawlerSites.task_id==task_id).dicts()
    if not site_data:
        raise HTTPException(400, 'Website Task not found')
    
    site_data = site_data[0]
    links = arguments.dict()['links']
    record = record[0]
    
    links = [{
        'type':'website',
        'name':link['url'],
        'bytes':0,
        'tokens':0,
        'meta':{'task_id':link['id']},
        'datastore_id':record['id'],
        'user_id':user_data['user_id'],
        'workspace_id':user_data['workspace_id'],
        'status':0,
        'created':time.time()
    } for link in links]
    
  
    with db.atomic():
        for batch in chunked(links, 500):
            DatastoresDocuments.insert_many(batch).execute()
        
    documents = DatastoresDocuments.select(DatastoresDocuments.id,DatastoresDocuments.meta).where(DatastoresDocuments.workspace_id==user_data['workspace_id'],
        DatastoresDocuments.datastore_id==record['id'],DatastoresDocuments.name.in_([link['name'] for link in links]),DatastoresDocuments.status==0).dicts()

        
    c_app.send_task(
        "semantic.upload_websites",
        kwargs={
            'records': list(documents), 
            'user':user_data,
            'datastore': record
        },queue="semantic",
    )
        
    return {'status':'ok'}