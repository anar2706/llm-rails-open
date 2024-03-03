import os
import json

environment = os.getenv('ENVIRONMENT')
semantic_name = 'semantic'


if environment == 'dev':
    semantic_name = 'semantic-dev'

rabbit_conf = json.loads(os.environ['app'])['rmq']
broker_url=f'amqp://{rabbit_conf[semantic_name]["user"]}:{rabbit_conf[semantic_name]["pass"]}@{rabbit_conf["host"]}:{rabbit_conf["port"]}/{rabbit_conf[semantic_name]["vhost"]}'
timezone = 'UTC'
task_default_exchange_type = 'direct'
broker_connection_retry_on_startup = True

task_routes = {
    'semantic.*':{'queue':'semantic'},
}
