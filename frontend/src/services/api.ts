import axios, { AxiosError } from 'axios'
import { GenerateRequest, GenerateResponse } from '../types'

// For Railway: Use relative path if VITE_API_BASE_URL is not set
// Railway's proxy will handle routing /api requests to backend service
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000')

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 seconds for AI generation
})

export async function generateContent(request: GenerateRequest): Promise<GenerateResponse> {
  try {
    const response = await apiClient.post<GenerateResponse>('/generate', request)
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail?: string }>
      const message = axiosError.response?.data?.detail || axiosError.message || 'Failed to generate content'
      throw new Error(message)
    }
    throw error
  }
}

// SSE streaming support
export function generateContentStream(
  request: GenerateRequest,
  onChunk: (chunk: string) => void,
  onComplete: (fullContent: string) => void,
  onError: (error: string) => void
) {
  const eventSource = new EventSource(
    `${API_BASE_URL}/generate/stream?${new URLSearchParams({
      data: JSON.stringify(request),
    })}`
  )

  let fullContent = ''

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      onComplete(fullContent)
      return
    }

    try {
      const data = JSON.parse(event.data)
      if (data.content) {
        fullContent += data.content
        onChunk(data.content)
      }
    } catch (e) {
      console.error('Failed to parse SSE data:', e)
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    onError('Stream connection error')
  }

  return () => eventSource.close()
}
