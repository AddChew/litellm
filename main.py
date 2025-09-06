import os
import uuid

os.environ["CONFIG_FILE_PATH"] = "test_config.yaml"

from ray import serve
from fastapi import Depends
from base64 import b64encode

from typing import Union, List, Dict, Optional
from litellm.secret_managers.main import get_secret_str
from litellm.proxy.proxy_server import app, premium_user

from litellm.proxy.auth.user_api_key_auth import user_api_key_auth
from litellm.proxy._types import PassThroughGenericEndpoint, CommonProxyErrors, LiteLLMRoutes
from litellm.proxy.pass_through_endpoints.pass_through_endpoints import InitPassThroughEndpointHelpers


def set_env_variables_in_header(custom_headers: Optional[dict]) -> Optional[dict]:
    """
    checks if any headers on config.yaml are defined as os.environ/COHERE_API_KEY etc

    only runs for headers defined on config.yaml

    example header can be

    {"Authorization": "bearer os.environ/COHERE_API_KEY"}
    """
    if custom_headers is None:
        return None
    headers = {}
    for key, value in custom_headers.items():
        # langfuse Api requires base64 encoded headers - it's simpleer to just ask litellm users to set their langfuse public and secret keys
        # we can then get the b64 encoded keys here
        if key == "LANGFUSE_PUBLIC_KEY" or key == "LANGFUSE_SECRET_KEY":
            # langfuse requires b64 encoded headers - we construct that here
            _langfuse_public_key = custom_headers["LANGFUSE_PUBLIC_KEY"]
            _langfuse_secret_key = custom_headers["LANGFUSE_SECRET_KEY"]
            if isinstance(
                _langfuse_public_key, str
            ) and _langfuse_public_key.startswith("os.environ/"):
                _langfuse_public_key = get_secret_str(_langfuse_public_key)
            if isinstance(
                _langfuse_secret_key, str
            ) and _langfuse_secret_key.startswith("os.environ/"):
                _langfuse_secret_key = get_secret_str(_langfuse_secret_key)
            headers["Authorization"] = "Basic " + b64encode(
                f"{_langfuse_public_key}:{_langfuse_secret_key}".encode("utf-8")
            ).decode("ascii")
        else:
            # for all other headers
            headers[key] = value
            if isinstance(value, str) and "os.environ/" in value:
                print(
                    "pass through endpoint - looking up 'os.environ/' variable"
                )
                # get string section that is os.environ/
                start_index = value.find("os.environ/")
                _variable_name = value[start_index:]

                print(
                    "pass through endpoint - getting secret for variable name: %s",
                    _variable_name,
                )
                _secret_value = get_secret_str(_variable_name)
                if _secret_value is not None:
                    new_value = value.replace(_variable_name, _secret_value)
                    headers[key] = new_value
    return headers


def initialize_pass_through_endpoints(
    app, pass_through_endpoints: Union[List[Dict], List[PassThroughGenericEndpoint]],
):
    """
    Initialize a list of pass-through endpoints by adding them to the FastAPI app routes

    Args:
        pass_through_endpoints: List of pass-through endpoints to initialize

    Returns:
        None
    """
    for endpoint in pass_through_endpoints:
        if isinstance(endpoint, PassThroughGenericEndpoint):
            endpoint = endpoint.model_dump()

        # Auto-generate ID for backwards compatibility if not present
        if endpoint.get("id") is None:
            endpoint["id"] = str(uuid.uuid4())

        _target = endpoint.get("target", None)
        _path: Optional[str] = endpoint.get("path", None)
        if _path is None:
            raise ValueError("Path is required for pass-through endpoint")
        _custom_headers = endpoint.get("headers", None)
        _custom_headers = set_env_variables_in_header(
            custom_headers=_custom_headers
        )
        _forward_headers = endpoint.get("forward_headers", None)
        _merge_query_params = endpoint.get("merge_query_params", None)
        _auth = endpoint.get("auth", None)
        _dependencies = None
        if _auth is not None and str(_auth).lower() == "true":
            if premium_user is not True:
                raise ValueError(
                    "Error Setting Authentication on Pass Through Endpoint: {}".format(
                        CommonProxyErrors.not_premium_user.value
                    )
                )
            _dependencies = [Depends(user_api_key_auth)]
            LiteLLMRoutes.openai_routes.value.append(_path)

        if _target is None:
            continue

        # Add exact path route
        InitPassThroughEndpointHelpers.add_exact_path_route(
            app=app,
            path=_path,
            target=_target,
            custom_headers=_custom_headers,
            forward_headers=_forward_headers,
            merge_query_params=_merge_query_params,
            dependencies=_dependencies,
            cost_per_request=endpoint.get("cost_per_request", None),
        )

        # Add wildcard route for sub-paths
        if endpoint.get("include_subpath", False) is True:
            InitPassThroughEndpointHelpers.add_subpath_route(
                app=app,
                path=_path,
                target=_target,
                custom_headers=_custom_headers,
                forward_headers=_forward_headers,
                merge_query_params=_merge_query_params,
                dependencies=_dependencies,
                cost_per_request=endpoint.get("cost_per_request", None),
            )
    return app


pass_through_endpoints = [{
    "path": "/v1/ocr/file",
    "target": "https://fake-json-api.mock.beeceptor.com/users",
    "forward_headers": True
}]
app = initialize_pass_through_endpoints(app, pass_through_endpoints)


@serve.deployment
@serve.ingress(app) # TODO: Bug is routes are not mounted yet at this point of ingress
class TestDeployment:
    pass

deployment = TestDeployment.bind()