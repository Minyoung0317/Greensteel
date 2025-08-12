# 🚀 GitHub 연동 Vercel 배포 가이드

## 📋 **배포 단계**

### **1단계: Vercel 프로젝트 생성**

1. **Vercel 대시보드 접속**
   - https://vercel.com/dashboard
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - GitHub 저장소: `Minyoung0317/Greensteel` 선택

3. **프로젝트 설정**
   ```
   Framework Preset: Other
   Root Directory: ./
   Build Command: npm run build
   Output Directory: frontend/.next
   Install Command: npm install
   ```

### **2단계: 환경 변수 설정**

Vercel 대시보드 → Settings → Environment Variables에서 설정:

```
NEXT_PUBLIC_API_BASE_URL=https://greensteel-gateway-production.up.railway.app
NODE_ENV=production
GATEWAY_URL=https://greensteel-gateway-production.up.railway.app
```

**중요**: `NEXT_PUBLIC_API_BASE_URL`은 실제 Railway에서 배포된 Gateway 서비스의 URL이어야 합니다.

### **3단계: Railway 백엔드 배포**

1. **Railway 프로젝트 생성**
   - https://railway.app 에서 새 프로젝트 생성
   - GitHub 저장소 연결

2. **Gateway 서비스 배포**
   - 서비스 타입: Web Service
   - 소스: GitHub 저장소
   - 디렉토리: `gateway`

3. **환경변수 설정**
   ```
   PORT=8080
   RAILWAY_ENVIRONMENT=true
   ```

4. **배포 URL 확인**
   - Railway 대시보드에서 생성된 URL 복사
   - 예: `https://greensteel-gateway-production.up.railway.app`

### **4단계: 자동 배포 설정**

1. **GitHub 연동 확인**
   - Vercel 프로젝트 설정에서 GitHub 연동 상태 확인
   - 자동 배포가 활성화되어 있는지 확인

2. **배포 트리거**
   - `main` 브랜치에 푸시하면 자동 배포
   - Pull Request 생성 시 프리뷰 배포

### **5단계: 배포 확인**

1. **배포 URL 확인**
   - Vercel 대시보드에서 배포 URL 확인
   - 예: `https://greensteel.vercel.app`

2. **배포 상태 확인**
   - Functions 탭에서 API 라우트 상태 확인
   - Logs 탭에서 배포 로그 확인

3. **CORS 설정 확인**
   - Gateway 서비스의 CORS 설정이 프론트엔드 도메인을 허용하는지 확인

## 🔧 **로컬 개발**

### **프론트엔드 실행**
```bash
cd frontend
npm install
npm run dev
```

### **Gateway API 실행**
```bash
cd gateway
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 📝 **배포 후 확인사항**

1. **프론트엔드 접속**
   - `https://greensteel.vercel.app`
   - `https://www.minyoung.cloud`

2. **API 엔드포인트 테스트**
   - `https://greensteel-gateway-production.up.railway.app/api/v1/user/health`

3. **환경 변수 확인**
   - Vercel 대시보드에서 환경 변수 설정 확인
   - Railway 대시보드에서 환경 변수 설정 확인

## 🚨 **문제 해결**

### **CORS 오류 해결**
1. Gateway 서비스의 CORS 설정 확인
2. 프론트엔드 도메인이 허용 목록에 포함되어 있는지 확인
3. Railway 환경변수 `RAILWAY_ENVIRONMENT=true` 설정

### **API 연결 오류 해결**
1. Railway Gateway 서비스가 정상 실행 중인지 확인
2. `NEXT_PUBLIC_API_BASE_URL`이 올바른 Railway URL로 설정되어 있는지 확인
3. Gateway 서비스의 health check 엔드포인트 접속 테스트

### **배포 실패 시**
1. Vercel 대시보드 → Functions 탭에서 에러 로그 확인
2. Railway 대시보드에서 서비스 로그 확인
3. GitHub Actions에서 빌드 로그 확인 