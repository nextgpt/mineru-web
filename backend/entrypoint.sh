#!/bin/bash

export MINERU_MODEL_SOURCE=local

if [ "$1" = "python" ]; then
  exec "$@"
else
  alembic upgrade head
  exec "$@"
fi 