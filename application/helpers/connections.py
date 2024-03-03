import os
import json
import redis
import weaviate

os.environ["TOKENIZERS_PARALLELISM"] = "false"
w_client = weaviate.Client(url=json.loads(os.environ['app'])['vector_db'])

MODELS = ['embedding-english-v1', 'embedding-multi-v1']


class Redis_Con:

    @property
    def red(self):
        creds = json.loads(os.environ['app'])['redis']
        return redis.StrictRedis(
            host=creds['host'], 
            password=creds['password'],
            port=creds['port'], 
            db=0
        )
    
red = Redis_Con().red