import type { NextApiRequest, NextApiResponse } from 'next'

type Data = {
  name: string
  message: string
  timestamp: string
  version: string
}

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<Data>
) {
  const data: Data = {
    name: '박민영',
    message: 'Hello from the API!',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  }
  
  res.status(200).json(data)
} 