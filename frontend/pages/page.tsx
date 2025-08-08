import React from 'react'
import Head from 'next/head'
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  return (
    <>
      <Head>
        <title>GreenSteel - 페이지</title>
        <meta name="description" content="GreenSteel 페이지" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* 헤더 */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-gray-900">GreenSteel</h1>
              </div>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
              >
                홈으로 돌아가기
              </button>
            </div>
          </div>
        </header>

        {/* 메인 콘텐츠 */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                로그인 성공!
              </h2>
              <p className="text-gray-600 mb-4">
                성공적으로 로그인되었습니다. 이제 GreenSteel 서비스를 이용하실 수 있습니다.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
                <div className="bg-green-50 p-6 rounded-lg border border-green-200">
                  <h3 className="text-lg font-medium text-green-800 mb-2">AI 채팅</h3>
                  <p className="text-green-600 text-sm">
                    AI와 대화하여 질문에 답변을 받아보세요.
                  </p>
                </div>
                
                <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
                  <h3 className="text-lg font-medium text-blue-800 mb-2">데이터 분석</h3>
                  <p className="text-blue-600 text-sm">
                    환경 데이터를 분석하고 인사이트를 얻어보세요.
                  </p>
                </div>
                
                <div className="bg-purple-50 p-6 rounded-lg border border-purple-200">
                  <h3 className="text-lg font-medium text-purple-800 mb-2">리포트 생성</h3>
                  <p className="text-purple-600 text-sm">
                    자동으로 환경 리포트를 생성해보세요.
                  </p>
                </div>
              </div>
              
              <div className="mt-8">
                <button
                  onClick={() => router.push('/')}
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors"
                >
                  채팅 시작하기
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  )
}
