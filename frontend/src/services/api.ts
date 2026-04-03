import axios, { AxiosError } from 'axios'
import { GenerateRequest, GenerateResponse } from '../types'

// Prefer same-origin `/api` when VITE_API_BASE_URL is unset:
// - Vite dev server proxies /api → http://localhost:8000 (see vite.config.ts)
// - Production nginx should proxy /api to the backend
// Set VITE_API_BASE_URL=http://localhost:8000 only if you need direct calls without a proxy.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 seconds for AI generation
})

/** Quick check that the backend is reachable (via /api/health when using the Vite proxy). */
export async function fetchBackendHealth(): Promise<boolean> {
  try {
    const r = await apiClient.get<{ status?: string }>('/health', { timeout: 5000 })
    return r.status === 200 && r.data?.status === 'healthy'
  } catch {
    return false
  }
}

export async function generateContent(request: GenerateRequest): Promise<GenerateResponse> {
  // region agent log
  fetch('http://127.0.0.1:7822/ingest/bf728b1b-4f52-40bb-a991-67ac1e5a030d',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'78b2f3'},body:JSON.stringify({sessionId:'78b2f3',location:'api.ts:generateContent',message:'pre_post',data:{apiBaseUrl:API_BASE_URL,postPath:'/generate',contentType:request.content_type},timestamp:Date.now(),hypothesisId:'H1',runId:'pre-fix'})}).catch(()=>{});
  // endregion
  try {
    const response = await apiClient.post<GenerateResponse>('/generate', request)
    // region agent log
    fetch('http://127.0.0.1:7822/ingest/bf728b1b-4f52-40bb-a991-67ac1e5a030d',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'78b2f3'},body:JSON.stringify({sessionId:'78b2f3',location:'api.ts:generateContent',message:'post_ok',data:{status:response.status},timestamp:Date.now(),hypothesisId:'H2',runId:'pre-fix'})}).catch(()=>{});
    // endregion
    return response.data
  } catch (error) {
    // region agent log
    if (axios.isAxiosError(error)) {
      const ax = error as AxiosError<{ detail?: string }>
      fetch('http://127.0.0.1:7822/ingest/bf728b1b-4f52-40bb-a991-67ac1e5a030d',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'78b2f3'},body:JSON.stringify({sessionId:'78b2f3',location:'api.ts:generateContent',message:'post_error',data:{code:ax.code,httpStatus:ax.response?.status,detail:ax.response?.data?.detail,msg:String(ax.message)},timestamp:Date.now(),hypothesisId:'H5',runId:'pre-fix'})}).catch(()=>{});
    }
    // endregion
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail?: string }>
      let message =
        axiosError.response?.data?.detail || axiosError.message || 'Failed to generate content'
      // Runtime evidence: ERR_NETWORK means no HTTP response (backend down, proxy cannot reach :8000, or dev server stopped).
      if (
        !axiosError.response &&
        (axiosError.code === 'ERR_NETWORK' || axiosError.message === 'Network Error')
      ) {
        message =
          'Cannot reach the API. Start the backend on port 8000 (e.g. from backend/: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000), keep the Vite dev server running, and use the default /api proxy unless VITE_API_BASE_URL points elsewhere.'
      }

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
