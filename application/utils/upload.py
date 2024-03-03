import os
import json
import boto3
import magic
import uuid
from botocore.exceptions import ClientError
from fastapi import HTTPException

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'upload')


def finfo(file):
    return magic.from_file(f'{UPLOAD_FOLDER}/{file}', mime=True)

def upload_text_file(text, original_name, datastore_id):
    file_name = uuid.uuid4().hex
    
    with open(f"{UPLOAD_FOLDER}/{file_name}", "w") as f:
        f.write(text)
        
    upload_to_aws(file_name, ['text/plain'], original_name, datastore_id)
    os.remove(os.path.join(UPLOAD_FOLDER,file_name))
    return file_name

def upload_to_aws(file_name, valid_formats, original_name, datastore_id):
    aws_data = json.loads(os.environ['app'])['aws']
    
    content_disposition = 'attachment;'
    if original_name:
        content_disposition+= f' filename="{original_name}"'

    content_type = finfo(file_name)
    print(f'content_type type {content_type}')

    if content_type not in valid_formats:
        os.remove(os.path.join(UPLOAD_FOLDER,file_name))
        raise HTTPException(400,f'Invalid File Format - {original_name}')

    s3_client = boto3.client('s3',
        endpoint_url=aws_data['internal'],
        aws_access_key_id=aws_data['access'],
        aws_secret_access_key=aws_data['secret'])

    try:
        with open(f"{UPLOAD_FOLDER}/{file_name}", "rb") as f:
            data = f.read()
            response = s3_client.put_object(ACL='public-read', Body=data, Bucket=aws_data['bucket'],
                ContentType=content_type, Key=f'{datastore_id}/{file_name}',ContentDisposition=content_disposition)
            
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return file_name, content_type
                
    except ClientError as e:
        print(f'error {e}')
        os.remove(os.path.join(UPLOAD_FOLDER,file_name))
        return 0
