# GreenSteel AI Assistant

AI 채팅 인터페이스 프로젝트입니다.

## 🚀 Vercel 배포

### 1. Vercel CLI 설치
```bash
npm i -g vercel
```

### 2. Vercel 로그인
```bash
vercel login
```

### 3. 프로젝트 배포
```bash
# 프로젝트 루트에서 실행
vercel

# 또는 프론트엔드 디렉토리에서 실행
cd frontend
vercel
```

### 4. 환경 변수 설정 (Vercel 대시보드에서)
- `NODE_ENV`: `production`
- `CUSTOM_KEY`: 필요한 경우 설정

## 🛠️ 로컬 개발

### 프론트엔드 실행
```bash
cd frontend
npm install
npm run dev
```

### 빌드
```bash
cd frontend
npm run build
npm start
```

## 📁 프로젝트 구조

```
greensteel/
├── frontend/          # Next.js 프론트엔드
│   ├── pages/        # 페이지 컴포넌트
│   ├── components/   # 재사용 컴포넌트
│   ├── styles/       # CSS 스타일
│   └── utils/        # 유틸리티 함수
├── gateway/          # API Gateway
└── service/          # 백엔드 서비스
```

## 🎨 주요 기능

- ✅ 어두운 테마 채팅 인터페이스
- ✅ 실시간 메시지 전송
- ✅ JSON 형태 데이터 변환
- ✅ 반응형 디자인
- ✅ Vercel 배포 지원

## 🔧 기술 스택

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python
- **Deployment**: Vercel

## 📝 라이센스

MIT License 