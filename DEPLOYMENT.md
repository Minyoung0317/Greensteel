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
GATEWAY_URL=https://your-gateway-api-url.vercel.app
NODE_ENV=production
```

### **3단계: 자동 배포 설정**

1. **GitHub 연동 확인**
   - Vercel 프로젝트 설정에서 GitHub 연동 상태 확인
   - 자동 배포가 활성화되어 있는지 확인

2. **배포 트리거**
   - `main` 브랜치에 푸시하면 자동 배포
   - Pull Request 생성 시 프리뷰 배포

### **4단계: 배포 확인**

1. **배포 URL 확인**
   - Vercel 대시보드에서 배포 URL 확인
   - 예: `https://greensteel.vercel.app`

2. **배포 상태 확인**
   - Functions 탭에서 API 라우트 상태 확인
   - Logs 탭에서 배포 로그 확인

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

2. **API 엔드포인트 테스트**
   - `https://greensteel.vercel.app/api/proxy/health`

3. **환경 변수 확인**
   - Vercel 대시보드에서 환경 변수 설정 확인

## 🚨 **문제 해결**

### **배포 실패 시**
1. Vercel 대시보드 → Functions 탭에서 에러 로그 확인
2. Build 로그에서 의존성 설치 문제 확인
3. 환경 변수 설정 확인

### **API 연결 실패 시**
1. Gateway API URL이 올바른지 확인
2. CORS 설정 확인
3. 네트워크 연결 상태 확인 