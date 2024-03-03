from project.celery import app


def send_usage_task(**kwargs):
    app.send_task(
        "semantic.openai_usage",
        kwargs=kwargs,
        queue="semantic",
    )