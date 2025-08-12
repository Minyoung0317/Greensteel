#!/bin/bash

# Railway 환경변수에서 포트 가져오기
PORT=${PORT:-8005}

echo "Starting Auth service on port $PORT"

# uvicorn 실행
uvicorn app.main:app --host 0.0.0.0 --port $PORT
