import os
import json
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry():
    sentry_creds = json.loads(os.environ['app'])['sentry']
    if sentry_creds:
        sentry_sdk.init(
            dsn=sentry_creds['url'],
            environment=sentry_creds['environment'],
            integrations=[
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            traces_sample_rate=1.0
        )