FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Node.js 설치
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# pnpm 설치
RUN npm install -g pnpm

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Gateway 코드 복사
COPY . .

# Frontend 의존성 설치 (볼륨 마운트로 처리)
WORKDIR /app

# 포트 노출
EXPOSE 8080

# 애플리케이션 실행
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
