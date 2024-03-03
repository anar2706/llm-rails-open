import os
import json
import requests

def load_environment():
    """ Loads environment variables from Vault """
    api_env_data = get_vault_data('llm-rails')
    os.environ['app'] = json.dumps(api_env_data)

def get_vault_data(path):
    """ Gets data from vault """
    url = os.environ.get('ENV_HOST')
    token = os.environ.get('ENV_TOKEN')

    if not url and token:
        send_log_slack_message('Url or Host not found')
        raise Exception('Url or Host not found')

    response = requests.get(url+path,headers={'X-Vault-Token':token})

    if response.status_code != 200:
        send_log_slack_message(f"""Credentials  not found wrong status code {url} {token}""")
        raise Exception(f'Credentials  not found wrong status code {url} {token}')

    data = json.loads(response.content)['data']['data']    
    os.environ['OPENAI_API_KEY'] = data['openai']

    return data


def send_log_slack_message(text):
    slack_url = os.environ['SLACK_URL']

    resp = requests.post(slack_url,json={
        "attachments": [
            {
                
                "text": f'```{text}```',
                "title": "LLM API",
                "mrkdwn_in": ["text"],
            }
        ],
        "text": ""
    })
