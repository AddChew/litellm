#!/bin/bash
# source activate litellm
export EXPERIMENTAL_MULTI_INSTANCE_RATE_LIMITING=true
export LITELLM_LOG=DEBUG

# export LITELLM_GLOBAL_MAX_PARALLEL_REQUEST_RETRIES=0 # TODO: this does not work
# export LITELLM_GLOBAL_MAX_PARALLEL_REQUEST_RETRY_TIMEOUT=0 # TODO: this does not work
# export DEFAULT_MAX_RETRIES=0 # TODO: this does not work

litellm --config config.yaml --host localhost --port 3010 & 
litellm --config config.yaml --host localhost --port 3011
# python3 fake_openai_server.py