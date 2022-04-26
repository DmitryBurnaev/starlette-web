#!/bin/sh
ls -lah /web-project

cd /web-project &&
flake8 --count && \
PYTHONPATH=$(pwd)/starlette_web coverage run --concurrency=thread,greenlet -m pytest && \
coverage report
