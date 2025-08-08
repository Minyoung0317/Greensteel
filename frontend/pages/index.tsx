import React, { useState } from 'react'
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
  const [inputValue, setInputValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [gatewayStatus, setGatewayStatus] = useState<GatewayStatus | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [currentView, setCurrentView] = useState<'chat' | 'login' | 'signup'>('chat')
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [loginData, setLoginData] = useState({ username: '', password: '' })
  const [signupData, setSignupData] = useState({ username: '', password: '' })
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authSuccess, setAuthSuccess] = useState('')
  const [lastResponse, setLastResponse] = useState<UserInputResponse | null>(null)
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)

  // API 기본 URL 설정 (환경에 따라 동적 설정)
  const getApiBaseUrl = () => {
    if (typeof window !== 'undefined') {
      // 클라이언트 사이드에서 환경 확인
      const hostname = window.location.hostname
      const protocol = window.location.protocol
      
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8080'
      } else {
        // Railway 또는 다른 프로덕션 환경
        return `${protocol}//${hostname}`
      }
    }
    // 서버 사이드에서는 기본값 사용
    return 'http://localhost:8080'
  }

  const createUserInputJSON = (message: string): UserInputData => {
    return {
      message: message.trim()
    }
  }

  // 로그인 핸들러
  const handleLoginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === 'username' || name === 'password') {
      setLoginData({
        ...loginData,
        [name]: value
      });
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const userData = {
      username: loginData.username,
      password: loginData.password
    };
    
    setAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');

    try {
      console.log('=== 로그인 API 요청 ===');
      console.log('요청 데이터:', JSON.stringify(userData, null, 2));
      
      const apiRequestData = {
        email: loginData.username,
        password: loginData.password
      };
      
      const apiBaseUrl = getApiBaseUrl();
      const response = await axios.post(`${apiBaseUrl}/api/v1/user/login`, apiRequestData);
      
      console.log('=== 로그인 API 응답 ===');
      console.log('응답 상태:', response.status);
      console.log('응답 데이터:', JSON.stringify(response.data, null, 2));
      
      setAuthSuccess(response.data.message || '로그인 성공!');
      setIsLoggedIn(true);
      setCurrentView('chat');
      
      setLoginData({
        username: '',
        password: ''
      });

    } catch (err: any) {
      console.log('=== 로그인 API 오류 ===');
      console.log('오류 상태:', err.response?.status);
      console.log('오류 데이터:', JSON.stringify(err.response?.data, null, 2));
      
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
    if (name === 'username' || name === 'password') {
      setSignupData({
        ...signupData,
        [name]: value
      });
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const signupUserData = {
      username: signupData.username,
      password: signupData.password
    };
    
    setAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');

    try {
      console.log('=== 회원가입 API 요청 ===');
      console.log('요청 데이터:', JSON.stringify(signupUserData, null, 2));
      
      const apiRequestData = {
        email: signupData.username,
        password: signupData.password
      };
      
      const apiBaseUrl = getApiBaseUrl();
      const response = await axios.post(`${apiBaseUrl}/api/v1/user/signup`, apiRequestData);
      
      console.log('=== 회원가입 API 응답 ===');
      console.log('응답 상태:', response.status);
      console.log('응답 데이터:', JSON.stringify(response.data, null, 2));
      
      setAuthSuccess(response.data.message || '회원가입 성공!');
      setCurrentView('login');
      
      setSignupData({
        username: '',
        password: ''
      });

    } catch (err: any) {
      console.log('=== 회원가입 API 오류 ===');
      console.log('오류 상태:', err.response?.status);
      console.log('오류 데이터:', JSON.stringify(err.response?.data, null, 2));
      
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
    
    setIsSubmitting(true)
    setError('')
    
    try {
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'user',
        content: inputValue,
        timestamp: new Date().toISOString()
      }

      // 사용자 메시지를 먼저 추가
      setMessages((prev) => [...prev, userMessage])
      
      // Gateway API로 사용자 입력 전송
      const userInputJSON = createUserInputJSON(inputValue)
      console.log('=== 사용자 입력 API 요청 ===')
      console.log('요청 데이터:', JSON.stringify(userInputJSON, null, 2))
      
      const apiBaseUrl = getApiBaseUrl();
      const response = await axios.post(`${apiBaseUrl}/api/v1/chatbot/process`, userInputJSON)
      
      console.log('=== 사용자 입력 API 응답 ===')
      console.log('응답 상태:', response.status)
      console.log('응답 데이터:', JSON.stringify(response.data, null, 2))
      
      // AI 응답 메시지 생성
      const assistantReply: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.response || `AI 응답: ${inputValue.trim()}에 대해 처리되었습니다.`,
        timestamp: new Date().toISOString()
      }

      // AI 응답 메시지 추가
      setMessages((prev) => [...prev, assistantReply])
      setInputValue('')
      
    } catch (err: any) {
      console.log('=== 사용자 입력 API 오류 ===')
      console.log('오류 상태:', err.response?.status)
      console.log('오류 데이터:', JSON.stringify(err.response?.data, null, 2))
      
      // 오류 발생 시에도 AI 응답 메시지 생성
      const assistantReply: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.',
        timestamp: new Date().toISOString()
      }
      
      setMessages((prev) => [...prev, assistantReply])
      setError(err.response?.data?.detail || '입력 처리 중 오류가 발생했습니다.')
      console.error('Error processing input:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  // 채팅 화면 렌더링 (ChatGPT 스타일)
  const renderChatForm = () => (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* 헤더 - 우측 상단에 로그인/회원가입 버튼 */}
      <header className="flex justify-between items-center p-6 border-b border-gray-200 bg-white shadow-sm">
        <div className="flex items-center">
          <h1 className="text-2xl font-bold text-gray-800">GreenSteel</h1>
        </div>
        <div className="flex items-center space-x-4">
          {!isLoggedIn ? (
            <>
              <button
                onClick={() => setCurrentView('login')}
                className="px-6 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors duration-200"
              >
                로그인
              </button>
              <button
                onClick={() => setCurrentView('signup')}
                className="px-6 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 font-medium transition-colors duration-200 shadow-md hover:shadow-lg"
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
                className="px-3 py-1 text-sm text-gray-500 hover:text-gray-700 transition-colors duration-200"
              >
                로그아웃
              </button>
            </div>
          )}
        </div>
      </header>

      {/* 메인 채팅 영역 */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        {/* 채팅 메시지 출력 영역 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">GreenSteel AI와 대화를 시작하세요</h3>
              <p className="text-gray-500 max-w-md">환경 친화적인 제철 기술에 대해 질문하거나 대화를 나누어보세요.</p>
            </div>
          )}
          {messages.length > 0 && messages.map((msg: ChatMessage) => (
            <div
              key={msg.id}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl px-6 py-4 rounded-2xl text-sm shadow-sm ${
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
        <div className="border-t border-gray-200 bg-white p-6">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex bg-white border-2 border-gray-200 rounded-2xl p-4 shadow-lg hover:shadow-xl transition-shadow duration-200 focus-within:border-green-500 focus-within:shadow-xl">
              <input
                type="text"
                value={inputValue}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputValue(e.target.value)}
                placeholder="메시지를 입력하세요..."
                className="flex-1 bg-transparent text-gray-800 outline-none placeholder-gray-400 text-base"
                disabled={isSubmitting}
              />
              <button
                type="submit"
                disabled={isSubmitting}
                className="ml-4 p-2 text-green-600 hover:text-green-700 disabled:opacity-50 transition-colors duration-200 rounded-full hover:bg-green-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )

  // 로그인 화면 렌더링
  const renderLoginForm = () => (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">GreenSteel</h1>
          <h2 className="text-2xl font-semibold text-gray-700">
            로그인
          </h2>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleLoginSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                이메일
              </label>
              <div className="mt-1">
                <input
                  id="username"
                  name="username"
                  type="email"
                  required
                  value={loginData.username}
                  onChange={handleLoginChange}
                  className="appearance-none block w-full px-4 py-3 border-2 border-gray-200 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 text-base transition-all duration-200"
                  placeholder="이메일을 입력하세요"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={loginData.password}
                  onChange={handleLoginChange}
                  className="appearance-none block w-full px-4 py-3 border-2 border-gray-200 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 text-base transition-all duration-200"
                  placeholder="비밀번호를 입력하세요"
                />
              </div>
            </div>

            {authError && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{authError}</div>
            )}

            {authSuccess && (
              <div className="text-green-600 text-sm bg-green-50 p-3 rounded-lg">{authSuccess}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={authLoading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-base font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 transition-all duration-200"
              >
                {authLoading ? '로그인 중...' : '로그인'}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setCurrentView('signup')}
                className="text-sm text-green-600 hover:text-green-500 transition-colors duration-200"
              >
                계정이 없으신가요? 회원가입
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )

  // 회원가입 화면 렌더링
  const renderSignupForm = () => (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">GreenSteel</h1>
          <h2 className="text-2xl font-semibold text-gray-700">
            회원가입
          </h2>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSignupSubmit}>
            <div>
              <label htmlFor="signup-username" className="block text-sm font-medium text-gray-700 mb-2">
                이메일
              </label>
              <div className="mt-1">
                <input
                  id="signup-username"
                  name="username"
                  type="email"
                  required
                  value={signupData.username}
                  onChange={handleSignupChange}
                  className="appearance-none block w-full px-4 py-3 border-2 border-gray-200 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 text-base transition-all duration-200"
                  placeholder="이메일을 입력하세요"
                />
              </div>
            </div>

            <div>
              <label htmlFor="signup-password" className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호
              </label>
              <div className="mt-1">
                <input
                  id="signup-password"
                  name="password"
                  type="password"
                  required
                  value={signupData.password}
                  onChange={handleSignupChange}
                  className="appearance-none block w-full px-4 py-3 border-2 border-gray-200 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 text-base transition-all duration-200"
                  placeholder="비밀번호를 입력하세요"
                />
              </div>
            </div>

            {authError && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{authError}</div>
            )}

            {authSuccess && (
              <div className="text-green-600 text-sm bg-green-50 p-3 rounded-lg">{authSuccess}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={authLoading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-base font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 transition-all duration-200"
              >
                {authLoading ? '회원가입 중...' : '회원가입'}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setCurrentView('login')}
                className="text-sm text-green-600 hover:text-green-500 transition-colors duration-200"
              >
                이미 계정이 있으신가요? 로그인
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )

  // 메인 렌더링
  return (
    <div>
      {currentView === 'chat' && renderChatForm()}
      {currentView === 'login' && renderLoginForm()}
      {currentView === 'signup' && renderSignupForm()}
    </div>
  )
}
