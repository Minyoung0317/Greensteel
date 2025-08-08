import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Gateway 서비스 시작 - 포트: {port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Railway에서는 reload=False 사용
    )
