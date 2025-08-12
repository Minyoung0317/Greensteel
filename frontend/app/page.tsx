'use client'

import { useState } from 'react'
import axios from 'axios'

export default function Home() {
  const [mode, setMode] = useState<'login' | 'signup' | 'logout'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value)
    setError('')
    setSuccess('')
  }

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value)
    setError('')
    setSuccess('')
  }

  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(e.target.value)
    setError('')
    setSuccess('')
  }

  const showNotification = (title: string, message: string) => {
    // 브라우저 알림 권한 확인 및 요청
    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification(title, { body: message })
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            new Notification(title, { body: message })
          }
        })
      }
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !password) {
      setError('이메일과 비밀번호를 입력해주세요.')
      return
    }

    setIsLoading(true)
    setError('')
    setSuccess('')

    try {
      console.log('=== 로그인 요청 시작 ===')
      console.log('요청 데이터:', { email, password })

      // 환경에 따른 API 엔드포인트 설정
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 
        (process.env.NODE_ENV === 'production' 
          ? 'https://greensteel-gateway-production-eeb5.up.railway.app'  // 실제 Railway Gateway URL
          : 'http://localhost:8080')
      
      const response = await axios.post(`${apiBaseUrl}/api/v1/auth/login`, {
        email,
        password
      }, {
        withCredentials: true  // 쿠키 포함
      })

      console.log('=== 로그인 응답 ===')
      console.log('응답 상태:', response.status)
      console.log('응답 데이터:', response.data)

      const successMessage = response.data.message || '로그인 성공!'
      setSuccess(successMessage)
      
      // 로그인 성공 시 브라우저 알림 표시
      showNotification('GreenSteel 로그인', successMessage)
      
      // 입력 필드 초기화
      setEmail('')
      setPassword('')

    } catch (err: any) {
      console.log('=== 로그인 오류 ===')
      console.log('오류 상태:', err.response?.status)
      console.log('오류 데이터:', err.response?.data)

      const errorMessage = err.response?.data?.detail || '로그인 중 오류가 발생했습니다.'
      setError(errorMessage)
      
      // 로그인 실패 시에도 알림 표시
      showNotification('GreenSteel 로그인', errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !password || !confirmPassword) {
      setError('모든 필드를 입력해주세요.')
      return
    }

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }

    if (password.length < 6) {
      setError('비밀번호는 6자 이상이어야 합니다.')
      return
    }

    setIsLoading(true)
    setError('')
    setSuccess('')

    try {
      console.log('=== 회원가입 요청 시작 ===')
      console.log('요청 데이터:', { email, password })

      // 환경에 따른 API 엔드포인트 설정
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 
        (process.env.NODE_ENV === 'production' 
          ? 'https://greensteel-gateway-production-eeb5.up.railway.app'  // 실제 Railway Gateway URL
          : 'http://localhost:8080')
      
      const response = await axios.post(`${apiBaseUrl}/api/v1/auth/signup`, {
        email,
        password
      }, {
        withCredentials: false  // 임시로 false로 설정
      })

      console.log('=== 회원가입 응답 ===')
      console.log('응답 상태:', response.status)
      console.log('응답 데이터:', response.data)

      const successMessage = response.data.message || '회원가입 성공!'
      setSuccess(successMessage)
      
      // 회원가입 성공 시 브라우저 알림 표시
      showNotification('GreenSteel 회원가입', successMessage)
      
      // 입력 필드 초기화
      setEmail('')
      setPassword('')
      setConfirmPassword('')

      // 로그인 모드로 전환
      setTimeout(() => {
        setMode('login')
        setSuccess('')
      }, 2000)

    } catch (err: any) {
      console.log('=== 회원가입 오류 ===')
      console.log('오류 상태:', err.response?.status)
      console.log('오류 데이터:', err.response?.data)

      const errorMessage = err.response?.data?.detail || '회원가입 중 오류가 발생했습니다.'
      setError(errorMessage)
      
      // 회원가입 실패 시에도 알림 표시
      showNotification('GreenSteel 회원가입', errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = async (e: React.FormEvent) => {
    e.preventDefault()
    
    setIsLoading(true)
    setError('')
    setSuccess('')

    try {
      console.log('=== 로그아웃 요청 시작 ===')

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 
        (process.env.NODE_ENV === 'production' 
          ? 'https://greensteel-gateway-production-eeb5.up.railway.app'
          : 'http://localhost:8080')
      
      const response = await axios.post(`${apiBaseUrl}/api/v1/auth/logout`, {}, {
        withCredentials: true  // 쿠키 포함
      })

      console.log('=== 로그아웃 응답 ===')
      console.log('응답 상태:', response.status)
      console.log('응답 데이터:', response.data)

      const successMessage = response.data.message || '로그아웃 성공!'
      setSuccess(successMessage)
      
      showNotification('GreenSteel 로그아웃', successMessage)
      
      // 입력 필드 초기화
      setEmail('')
      setPassword('')

    } catch (err: any) {
      console.log('=== 로그아웃 오류 ===')
      console.log('오류 상태:', err.response?.status)
      console.log('오류 데이터:', err.response?.data)

      const errorMessage = err.response?.data?.detail || '로그아웃 중 오류가 발생했습니다.'
      setError(errorMessage)
      
      showNotification('GreenSteel 로그아웃', errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const switchMode = () => {
    if (mode === 'login') {
      setMode('signup')
    } else if (mode === 'signup') {
      setMode('logout')
    } else {
      setMode('login')
    }
    setEmail('')
    setPassword('')
    setConfirmPassword('')
    setError('')
    setSuccess('')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-4xl bg-white shadow-xl rounded-xl flex overflow-hidden">
        {/* 왼쪽 패널 - 그라데이션 배경 */}
        <div className="w-1/2 bg-gradient-to-br from-green-600 to-green-800"></div>

        {/* 로그인/회원가입 패널 */}
        <div className="w-1/2 p-10 flex flex-col justify-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">Greensteel</h1>

          <form onSubmit={mode === 'login' ? handleLogin : mode === 'signup' ? handleSignup : handleLogout}>
            <input
              type="email"
              placeholder="이메일을 입력하세요."
              value={email}
              onChange={handleEmailChange}
              className="border border-gray-300 rounded-lg px-4 py-2 mb-4 w-full focus:outline-none focus:ring-2 focus:ring-green-400"
              disabled={isLoading}
            />
            <input
              type="password"
              placeholder="비밀번호를 입력하세요."
              value={password}
              onChange={handlePasswordChange}
              className="border border-gray-300 rounded-lg px-4 py-2 mb-4 w-full focus:outline-none focus:ring-2 focus:ring-green-400"
              disabled={isLoading}
            />
            
            {mode === 'signup' && (
              <input
                type="password"
                placeholder="비밀번호를 다시 입력하세요."
                value={confirmPassword}
                onChange={handleConfirmPasswordChange}
                className="border border-gray-300 rounded-lg px-4 py-2 mb-4 w-full focus:outline-none focus:ring-2 focus:ring-green-400"
                disabled={isLoading}
              />
            )}

            {mode === 'login' && (
              <div className="flex items-center mb-4">
                <input type="checkbox" id="remember" className="mr-2" />
                <label htmlFor="remember" className="text-sm text-gray-600">
                  아이디 저장
                </label>
              </div>
            )}

            {mode === 'logout' && (
              <div className="mb-4 p-3 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded">
                로그아웃을 진행하시겠습니까?
              </div>
            )}

            {/* 에러 메시지 */}
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            )}

            {/* 성공 메시지 */}
            {success && (
              <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                {success}
              </div>
            )}

            <button 
              type="submit"
              disabled={isLoading}
              className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading 
                ? (mode === 'login' ? '로그인 중...' : mode === 'signup' ? '회원가입 중...' : '로그아웃 중...') 
                : (mode === 'login' ? '로그인' : mode === 'signup' ? '회원가입' : '로그아웃')}
            </button>
          </form>

          <div className="mt-6 flex justify-between text-sm text-gray-500">
            <button 
              onClick={switchMode}
              className="hover:underline text-green-600"
            >
              {mode === 'login' ? '회원가입하기' : mode === 'signup' ? '로그아웃하기' : '로그인하기'}
            </button>
            {mode === 'login' && (
              <a href="#" className="hover:underline">
                비밀번호 찾기
              </a>
            )}
          </div>

          <div className="text-xs text-gray-400 mt-10">
            최적의 솔루션 파트너는 GREENSTEEL입니다.
            <br />
            <span className="block mt-1"> https://www.minyoung.cloud/ | Tel : 010-2208-5322</span>
          </div>
        </div>
      </div>
    </div>
  );
}
