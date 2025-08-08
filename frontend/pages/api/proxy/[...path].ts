import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { path } = req.query
  const apiPath = Array.isArray(path) ? path.join('/') : path || ''
  
  // Gateway API URL (로컬 개발용)
  const gatewayUrl = process.env.GATEWAY_URL || 'http://localhost:8080'
  
  try {
    const response = await fetch(`${gatewayUrl}/api/v1/${apiPath}`, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        ...req.headers as Record<string, string>
      },
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined
    })
    
    const data = await response.json()
    
    res.status(response.status).json(data)
  } catch (error) {
    console.error('Proxy error:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
} 