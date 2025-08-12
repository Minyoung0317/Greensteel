#!/bin/bash

# Railway 환경변수에서 포트 가져오기
PORT=${PORT:-8080}

echo "Starting Gateway service on port $PORT"

# uvicorn 실행
cd gateway && uvicorn app.main:app --host 0.0.0.0 --port $PORT
