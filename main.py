import os
import yaml
import asyncio
import functools

os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["CONFIG_FILE_PATH"] = "test_config.yaml"

from ray import serve
from litellm.proxy.proxy_server import app
from litellm.proxy.pass_through_endpoints.pass_through_endpoints import initialize_pass_through_endpoints


def force_sync(fn):
    """
    turn an async function to sync function
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        res = fn(*args, **kwargs)
        if asyncio.iscoroutine(res):
            return asyncio.get_event_loop().run_until_complete(res)
        return res

    return wrapper


with open(os.getenv("CONFIG_FILE_PATH", "test_config.yaml"), "r") as f:
    pass_through_endpoints = yaml.safe_load(f).get("general_settings", {}).get("pass_through_endpoints", [])

force_sync(initialize_pass_through_endpoints)(pass_through_endpoints)


@serve.deployment
@serve.ingress(app)
class TestDeployment:
    pass

deployment = TestDeployment.bind()