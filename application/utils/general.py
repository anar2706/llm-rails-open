import uuid
import time
import asyncio
import hashlib
import tiktoken

def timefn(func):
    async def wrapper_async(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Function {func.__name__} took {end_time - start_time:.5f} seconds to complete.")
        return result

    def wrapper_sync(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Function {func.__name__} took {end_time - start_time:.5f} seconds to complete.")
        return result

    return wrapper_async if asyncio.iscoroutinefunction(func) else wrapper_sync


def generate_uuid():
    return str(uuid.uuid4())


def generate_md5(text):
    return hashlib.md5(text.encode()).hexdigest()


def num_tokens_from_messages(text,model):
    """Returns the number of tokens used by a list of messages."""
    encoding = tiktoken.encoding_for_model(model)

    if model == "gpt-3.5-turbo":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
    
    elif model == "gpt-4":
        tokens_per_message = 3

    elif model == "gpt-3.5-turbo-16k":
        tokens_per_message = 3
    
    num_tokens = 0
    num_tokens += tokens_per_message
    num_tokens += len(encoding.encode(text))

    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens