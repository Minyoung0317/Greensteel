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
      
      const response = await axios.post('http://localhost:8080/api/v1/user/login', apiRequestData);
      
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
      
      const response = await axios.post('http://localhost:8080/api/v1/user/signup', apiRequestData);
      
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
      setMessages(prev => [...prev, userMessage])
      
      // Gateway API로 사용자 입력 전송
      const userInputJSON = createUserInputJSON(inputValue)
      console.log('=== 사용자 입력 API 요청 ===')
      console.log('요청 데이터:', JSON.stringify(userInputJSON, null, 2))
      
      const response = await axios.post('http://localhost:8080/api/v1/chatbot/process', userInputJSON)
      
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
      setMessages(prev => [...prev, assistantReply])
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
      
      setMessages(prev => [...prev, assistantReply])
      setError(err.response?.data?.detail || '입력 처리 중 오류가 발생했습니다.')
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
    </div>
  )

  // 로그인 화면 렌더링
  const renderLoginForm = () => (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          로그인
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleLoginSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
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
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                  placeholder="이메일을 입력하세요"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
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
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                  placeholder="비밀번호를 입력하세요"
                />
              </div>
            </div>

            {authError && (
              <div className="text-red-600 text-sm">{authError}</div>
            )}

            {authSuccess && (
              <div className="text-green-600 text-sm">{authSuccess}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={authLoading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              >
                {authLoading ? '로그인 중...' : '로그인'}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setCurrentView('signup')}
                className="text-sm text-green-600 hover:text-green-500"
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
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          회원가입
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSignupSubmit}>
            <div>
              <label htmlFor="signup-username" className="block text-sm font-medium text-gray-700">
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
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                  placeholder="이메일을 입력하세요"
                />
              </div>
            </div>

            <div>
              <label htmlFor="signup-password" className="block text-sm font-medium text-gray-700">
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
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                  placeholder="비밀번호를 입력하세요"
                />
              </div>
            </div>

            {authError && (
              <div className="text-red-600 text-sm">{authError}</div>
            )}

            {authSuccess && (
              <div className="text-green-600 text-sm">{authSuccess}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={authLoading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              >
                {authLoading ? '회원가입 중...' : '회원가입'}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setCurrentView('login')}
                className="text-sm text-green-600 hover:text-green-500"
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
