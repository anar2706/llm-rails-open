import os
import json
from peewee import *
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
        mysql_config = json.loads(os.environ['app'])['mysql']['crawl']

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


class CrawlerSites(BaseModel):
    report = JSONField(null=True)  # json
    requests = IntegerField(null=True)
    status = IntegerField(constraints=[SQL("DEFAULT 0")])
    strategy = CharField(null=True)
    task_id = CharField()
    total = IntegerField(constraints=[SQL("DEFAULT 0")])
    url = CharField()

    class Meta:
        table_name = 'crawler_sites'

class CrawlerTasks(BaseModel):
    data = TextField(null=True)
    status = IntegerField(null=True)
    task_id = CharField(index=True, null=True)
    url = CharField(null=True)

    class Meta:
        table_name = 'crawler_tasks'

