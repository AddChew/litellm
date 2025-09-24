#!/bin/bash
# source activate litellm
export EXPERIMENTAL_MULTI_INSTANCE_RATE_LIMITING=true

litellm --config config.yaml --host localhost --port 3001 & 
litellm --config config.yaml --host localhost --port 3002