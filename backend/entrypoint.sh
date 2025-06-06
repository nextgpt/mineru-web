#!/bin/bash

source /opt/mineru_venv/bin/activate

if [ "$1" = "python" ]; then
  exec "$@"
else
  alembic upgrade head
  exec "$@"
fi 