import os
import json
from peewee import *
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin
from application.helpers.core import load_environment
from playhouse.sqlite_ext import JSONField

def db_value(_ : JSONField, value):
        if value is not None:
            return json.dumps(value)

def python_value(_ : JSONField, value):
    if value is not None:
        return json.loads(value)

JSONField.db_value = db_value
JSONField.python_value = python_value

if not os.environ.get('app'):
    load_environment()

class RetryMySQLDatabase(ReconnectMixin, MySQLDatabase):
    _instance = None
 
    @staticmethod
    def get_db_instance():
        mysql_config = json.loads(os.environ['app'])['mysql']['main']

        if not RetryMySQLDatabase._instance:
            RetryMySQLDatabase._instance = RetryMySQLDatabase(
                    mysql_config['name'],
                    user=mysql_config['user'],
                    password=mysql_config['pass'],
                    host=mysql_config['host'],
                    port=int(mysql_config['port']),
                    charset='utf8mb4'
                )
            
        return RetryMySQLDatabase._instance


db = RetryMySQLDatabase.get_db_instance()

class BaseModel(Model):
    class Meta:
        database = db


class ApiKeys(BaseModel):
    created = IntegerField()
    is_internal = IntegerField(constraints=[SQL("DEFAULT 0")])
    key = CharField(unique=True)
    name = CharField()
    status = IntegerField(constraints=[SQL("DEFAULT 1")])
    user_id = IntegerField()
    workspace_id = IntegerField()

    class Meta:
        table_name = 'api_keys'

class ChatApps(BaseModel):
    chat_model = CharField()
    configs = JSONField()  # json
    created = IntegerField()
    datastore_id = IntegerField(null=True)
    icon = CharField(null=True)
    input_configs = JSONField(null=True)  # json
    name = CharField()
    pid = CharField()
    prompt = TextField()
    type = CharField()
    updated = IntegerField(null=True)
    user_id = IntegerField()
    welcome_message = TextField(null=True)
    widget_configs = JSONField(null=True)  # json
    workspace_id = IntegerField()

    class Meta:
        table_name = 'chat_apps'

class ChatFeedbacks(BaseModel):
    app_id = IntegerField()
    created = IntegerField()
    message_id = IntegerField()
    rating = IntegerField()
    session_id = IntegerField()

    class Meta:
        table_name = 'chat_feedbacks'

class ChatMessages(BaseModel):
    created = IntegerField()
    message = TextField()
    pid = CharField()
    session_id = IntegerField()
    sources = JSONField(null=True)  # json
    type = IntegerField()

    class Meta:
        table_name = 'chat_messages'

class ChatSessions(BaseModel):
    app_id = IntegerField()
    created = IntegerField()
    internal_user_id = IntegerField(null=True)
    session_pid = CharField()
    total_messages = IntegerField(constraints=[SQL("DEFAULT 0")])
    updated = IntegerField()
    user_pid = CharField()
    workspace_id = IntegerField()

    class Meta:
        table_name = 'chat_sessions'

class Datastores(BaseModel):
    attributes = JSONField()  # json
    created = IntegerField()
    description = CharField(null=True)
    embedding_model = CharField()
    name = CharField()
    pid = CharField()
    total_bytes = BigIntegerField(constraints=[SQL("DEFAULT 0")])
    total_docs = IntegerField(constraints=[SQL("DEFAULT 0")])
    total_tokens = IntegerField(constraints=[SQL("DEFAULT 0")])
    user_id = IntegerField()
    vector_id = CharField()
    workspace_id = IntegerField()

    class Meta:
        table_name = 'datastores'

class DatastoresDocuments(BaseModel):
    bytes = IntegerField(constraints=[SQL("DEFAULT 0")])
    created = IntegerField()
    datastore_id = IntegerField()
    meta = JSONField(null=True)  # json
    name = CharField()
    status = IntegerField(constraints=[SQL("DEFAULT 0")])
    tokens = IntegerField(constraints=[SQL("DEFAULT 0")])
    type = CharField()
    user_id = IntegerField()
    workspace_id = IntegerField()

    class Meta:
        table_name = 'datastores_documents'

class EmbeddingsLogs(BaseModel):
    created = IntegerField(null=True)
    model = CharField(null=True)
    text = JSONField(null=True)
    user_id = IntegerField(null=True)
    workspace_id = IntegerField(null=True)

    class Meta:
        table_name = 'embeddings_logs'

class SearchLogs(BaseModel):
    created = IntegerField(null=True)
    text = TextField()
    type = CharField()
    datastore_id = IntegerField(null=True)
    user_id = IntegerField(null=True)
    workspace_id = IntegerField(null=True)

    class Meta:
        table_name = 'search_logs'

class Usage(BaseModel):
    api_id = IntegerField()
    created = IntegerField(null=True)
    meta = JSONField(null=True)  # json
    quantity = IntegerField()
    subtype = CharField(null=True)
    type = CharField()
    unit = CharField()
    workspace_id = IntegerField()

    class Meta:
        table_name = 'usage'

class Users(BaseModel):
    active = IntegerField(constraints=[SQL("DEFAULT 1")])
    created = IntegerField()
    email = CharField()
    hash = CharField(null=True)
    lastname = CharField()
    name = CharField()
    salt = CharField(null=True)
    type = IntegerField(constraints=[SQL("DEFAULT 1")])
    workspace_id = IntegerField()

    class Meta:
        table_name = 'users'

class UsersLogs(BaseModel):
    created_at = IntegerField()
    created_by = IntegerField()
    data = JSONField()  # json
    type = CharField()

    class Meta:
        table_name = 'users_logs'

class UsersOauth(BaseModel):
    created = IntegerField()
    email = CharField()
    meta = JSONField(null=True)  # json
    provider = CharField(null=True)
    uid = CharField(null=True)
    user_id = CharField()
    workspace_id = IntegerField()

    class Meta:
        table_name = 'users_oauth'

class UsersVerifications(BaseModel):
    active = IntegerField(constraints=[SQL("DEFAULT 1")])
    code = CharField()
    created = IntegerField()
    type = CharField()
    user_id = IntegerField()
    workspace_id = IntegerField()

    class Meta:
        table_name = 'users_verifications'

class Workspaces(BaseModel):
    active = IntegerField(constraints=[SQL("DEFAULT 0")])
    billing_id = CharField(null=True)
    created_at = IntegerField()
    name = CharField()
    pid = CharField()

    class Meta:
        table_name = 'workspaces'

