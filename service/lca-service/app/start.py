#!/usr/bin/env python3
"""
LCA Service 시작 스크립트
고정 포트 8084로 실행
"""

import uvicorn
import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 LCA Service 시작 중...")
    print(f"포트: 8084")
    print(f"환경: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') == 'true' else 'Local/Docker'}")
    
    # 고정 포트로 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8084,
        reload=False,
        log_level="info"
    )
