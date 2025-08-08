import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import { useRouter } from 'next/router'
import axios from 'axios'

interface GatewayStatus {
  message: string
  version: string
  environment: string
  timestamp: string
  services: {
    discovery: string
    proxy: string
  }
  docs: {
    swagger: string
    redoc: string
    openapi: string
  }
}

interface ApiError {
  message: string
  response?: {
    status: number
    data: unknown
  }
}

interface UserInputResponse {
  status: string
  message: string
  received_input: string
  timestamp: string
  processing_time: number
}

interface UserInputData {
  message: string
}

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface LoginData {
  username: string
  password: string
}

interface SignupData {
  username: string
  password: string
}

export default function Home() {
  const router = useRouter()
  const [status, setStatus] = useState<GatewayStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [lastResponse, setLastResponse] = useState<UserInputResponse | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  
  // 로그인/회원가입 상태
  const [currentView, setCurrentView] = useState<'chat' | 'login' | 'signup'>('chat')
  const [loginData, setLoginData] = useState<LoginData>({ username: '', password: '' })
  const [signupData, setSignupData] = useState<SignupData>({ username: '', password: '' })
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authSuccess, setAuthSuccess] = useState('')
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const createUserInputJSON = (message: string): UserInputData => {
    return {
      message: message.trim()
    }
  }

  // 로그인 핸들러
  const handleLoginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setLoginData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // JSON 형태로 alert 창 표시
    const userData = {
      username: loginData.username,
      password: loginData.password
    };
    alert(JSON.stringify(userData, null, 2));
    
    setAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');

    try {
      console.log('=== 로그인 API 요청 ===');
      console.log('요청 데이터:', JSON.stringify(userData, null, 2));
      
      // 백엔드 API와 맞춰서 email로 변경
      const apiRequestData = {
        email: loginData.username,
        password: loginData.password
      };
      
      // Gateway API 호출
      const response = await axios.post('http://localhost:8080/api/v1/user/login', apiRequestData);
      
      console.log('=== 로그인 API 응답 ===');
      console.log('응답 상태:', response.status);
      console.log('응답 데이터:', JSON.stringify(response.data, null, 2));
      console.log('========================');
      
      setAuthSuccess(response.data.message || '로그인 성공!');
      setIsLoggedIn(true);
      setCurrentView('chat');
      
      // 폼 초기화
      setLoginData({
        username: '',
        password: ''
      });

      // 페이지 이동 (예: /page.tsx로 이동)
      router.push('/page');

    } catch (err: any) {
      console.log('=== 로그인 API 오류 ===');
      console.log('오류 상태:', err.response?.status);
      console.log('오류 데이터:', JSON.stringify(err.response?.data, null, 2));
      console.log('========================');
      
      const errorMessage = err.response?.data?.detail || '로그인 중 오류가 발생했습니다.';
      setAuthError(errorMessage);
      console.error('Login error:', err);
    } finally {
      setAuthLoading(false);
    }
  };

  // 회원가입 핸들러
  const handleSignupChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setSignupData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // JSON 형태로 alert 창 표시
    const signupUserData = {
      username: signupData.username,
      password: signupData.password
    };
    alert(JSON.stringify(signupUserData, null, 2));
    
    setAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');

    try {
      console.log('=== 회원가입 API 요청 ===');
      console.log('요청 데이터:', JSON.stringify(signupUserData, null, 2));
      
      // 백엔드 API와 맞춰서 email로 변경
      const apiRequestData = {
        email: signupData.username,
        password: signupData.password
      };
      
      // Gateway API 호출
      const response = await axios.post('http://localhost:8080/api/v1/user/signup', apiRequestData);
      
      console.log('=== 회원가입 API 응답 ===');
      console.log('응답 상태:', response.status);
      console.log('응답 데이터:', JSON.stringify(response.data, null, 2));
      console.log('========================');
      
      setAuthSuccess(response.data.message || '회원가입이 완료되었습니다!');
      
      // 폼 초기화
      setSignupData({
        username: '',
        password: ''
      });

    } catch (err: any) {
      console.log('=== 회원가입 API 오류 ===');
      console.log('오류 상태:', err.response?.status);
      console.log('오류 데이터:', JSON.stringify(err.response?.data, null, 2));
      console.log('========================');
      
      const errorMessage = err.response?.data?.detail || '회원가입 중 오류가 발생했습니다.';
      setAuthError(errorMessage);
      console.error('Signup error:', err);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!inputValue.trim()) return

    try {
      setIsSubmitting(true)
      setError(null)

      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'user',
        content: inputValue.trim(),
        timestamp: new Date().toISOString()
      }

      const assistantReply: ChatMessage = {
        id: `${Date.now()}-ai`,
        type: 'assistant',
        content: `AI 응답: ${inputValue.trim()}에 대해 생각해볼게요.`,
        timestamp: new Date().toISOString()
      }

      setMessages((prev) => [...prev, userMessage, assistantReply])
      const userInputJSON = createUserInputJSON(inputValue)
      console.log('사용자 입력 JSON:', JSON.stringify(userInputJSON, null, 2))
      setInputValue('')
    } catch (err: unknown) {
      const apiError = err as ApiError
      setError(apiError.message || '입력 처리 중 오류가 발생했습니다.')
      console.error('Error processing input:', err)
    } finally {
      setIsSubmitting(false)
    }
  }



  // 채팅 화면 렌더링 (ChatGPT 스타일)
  const renderChatForm = () => (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* 헤더 - 우측 상단에 로그인/회원가입 버튼 */}
      <header className="flex justify-between items-center p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center">
          <h1 className="text-xl font-semibold text-gray-800">GreenSteel</h1>
        </div>
        <div className="flex items-center space-x-4">
          {!isLoggedIn ? (
            <>
              <button
                onClick={() => setCurrentView('login')}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
              >
                로그인
              </button>
              <button
                onClick={() => setCurrentView('signup')}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
              >
                회원가입
              </button>
            </>
          ) : (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">환영합니다!</span>
              <button
                onClick={() => {
                  setIsLoggedIn(false);
                  setCurrentView('login');
                }}
                className="px-3 py-1 text-sm text-gray-500 hover:text-gray-700"
              >
                로그아웃
              </button>
            </div>
          )}
        </div>
      </header>

      {/* 메인 채팅 영역 */}
      <div className="flex-1 flex flex-col">
        {/* 채팅 메시지 출력 영역 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length > 0 && messages.map((msg: ChatMessage) => (
            <div
              key={msg.id}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-xl text-sm ${
                  msg.type === 'user'
                    ? 'bg-green-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        {/* 입력창 */}
        <div className="border-t border-gray-200 bg-white p-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex bg-white border border-gray-300 rounded-xl p-4 shadow-sm">
              <input
                type="text"
                value={inputValue}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputValue(e.target.value)}
                placeholder="메시지를 입력하세요..."
                className="flex-1 bg-transparent text-gray-800 outline-none placeholder-gray-400"
                disabled={isSubmitting}
              />
              <button
                type="submit"
                disabled={isSubmitting}
                className="ml-4 text-green-600 hover:text-green-700 disabled:opacity-50"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
          <div className="bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      <Head>
        <title>GreenSteel - AI Assistant</title>
        <meta name="description" content="AI Assistant Interface" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      {currentView === 'chat' && renderChatForm()}
      
      {/* 로그인 모달 */}
      {currentView === 'login' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">로그인</h2>
              <button
                onClick={() => setCurrentView('chat')}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                  사용자명
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="사용자명을 입력하세요"
                  value={loginData.username}
                  onChange={handleLoginChange}
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  비밀번호
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="비밀번호"
                  value={loginData.password}
                  onChange={handleLoginChange}
                />
              </div>
              {authError && (
                <div className="text-red-500 text-sm">{authError}</div>
              )}
              {authSuccess && (
                <div className="text-green-500 text-sm">{authSuccess}</div>
              )}
              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {authLoading ? '로그인 중...' : '로그인'}
              </button>
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setCurrentView('signup')}
                  className="text-green-600 hover:text-green-700 text-sm"
                >
                  계정이 없으신가요? 회원가입
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* 회원가입 모달 */}
      {currentView === 'signup' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">회원가입</h2>
              <button
                onClick={() => setCurrentView('chat')}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleSignupSubmit} className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                  사용자명 *
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="사용자명을 입력하세요"
                  value={signupData.username}
                  onChange={handleSignupChange}
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  비밀번호 *
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="비밀번호를 입력하세요"
                  value={signupData.password}
                  onChange={handleSignupChange}
                />
              </div>
              {authError && (
                <div className="text-red-500 text-sm">{authError}</div>
              )}
              {authSuccess && (
                <div className="text-green-500 text-sm">{authSuccess}</div>
              )}
              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {authLoading ? '처리 중...' : '회원가입'}
              </button>
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setCurrentView('login')}
                  className="text-green-600 hover:text-green-700 text-sm"
                >
                  이미 계정이 있으신가요? 로그인
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
} 
