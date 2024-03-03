import json
import hashlib
from application.helpers.connections import red


class Embeddingcache:


    @staticmethod
    def set_cache(arguments, response):
        input = arguments.input
        if isinstance(arguments.input, str):
            input = [input]

        texts = [t.replace("\n", " ") for t in input]
        text  = ' '.join(texts).strip().lower()

        key = f'{arguments.model}:{text}'
        hash_md5 = hashlib.md5(key.encode('utf-8')).hexdigest()

        red.setex(hash_md5, 604800, json.dumps(response))

    
    @staticmethod
    def get_cache(arguments):
        input = arguments.input
        if isinstance(arguments.input, str):
            input = [input]
       
        texts = [t.replace("\n", " ") for t in input]
        text  = ' '.join(texts).strip().lower()

        key = f'{arguments.model}:{text}'
        hash_md5 = hashlib.md5(key.encode('utf-8')).hexdigest()
        
        resp = red.get(hash_md5)
        return json.loads(resp) if resp else resp