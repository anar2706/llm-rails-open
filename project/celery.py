import os
import json
from celery import Celery
from celery_slack import Slackify
from application.helpers.core import load_environment, send_log_slack_message

if not os.getenv('app'):
    load_environment()

from project import celeryconfig

SLACK_WEBHOOK = os.environ.get('SLACK_URL')

app = Celery('project',include=['project.tasks'])
app.config_from_object(celeryconfig)

rabbit_conf = json.loads(os.environ['app'])['rmq']

DEFAULT_OPTIONS = {
    "slack_beat_init_color": "#FFCC2B",
    "slack_broker_connect_color": "#36A64F",
    "slack_broker_disconnect_color": "#D00001",
    "slack_celery_startup_color": "#FFCC2B",
    "slack_celery_shutdown_color": "#660033",
    "slack_task_prerun_color": "#D3D3D3",
    "slack_task_success_color": "#36A64F",
    "slack_task_failure_color": "#D00001",
    "slack_request_timeout": 1,
    "flower_base_url": None,
    "show_celery_hostname": False,
    "show_task_id": True,
    "show_task_execution_time": True,
    "show_task_args": True,
    "show_task_kwargs": True,
    "show_task_exception_info": True,
    "show_task_return_value": True,
    "show_task_prerun": False,
    "show_startup": True,
    "show_shutdown": True,
    "show_beat": True,
    "show_broker": False,
    "use_fixed_width": True,
    "include_tasks": None,
    "exclude_tasks": None,
    "failures_only": True,
    "beat_schedule": None,
    "beat_show_full_task_path": False,
}

parser_app = Celery('parser')
parser_app.config_from_object({
    'broker_url':f'amqp://{rabbit_conf["parser"]["user"]}:{rabbit_conf["parser"]["pass"]}@{rabbit_conf["host"]}:{rabbit_conf["port"]}/{rabbit_conf["parser"]["vhost"]}'

})

if SLACK_WEBHOOK:
    slack_app = Slackify(app, SLACK_WEBHOOK, **DEFAULT_OPTIONS)
