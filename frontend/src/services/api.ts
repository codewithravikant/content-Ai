import axios, { AxiosError } from 'axios'
import { GenerateRequest, GenerateResponse } from '../types'

// Prefer same-origin `/api` when VITE_API_BASE_URL is unset:
// - Vite dev server proxies /api → http://localhost:8000 (see vite.config.ts)
// - Production nginx should proxy /api to the backend
// Set VITE_API_BASE_URL=http://localhost:8000 only if you need direct calls without a proxy.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const clientApiKey = import.meta.env.VITE_CLIENT_API_KEY?.trim()

/** Opaque session from POST /auth/email/verify; takes precedence over VITE_CLIENT_API_KEY when set. */
export const EMAIL_SESSION_KEY = 'ghostwriter_email_session'

function bearerForRequests(): string | undefined {
  if (typeof localStorage === 'undefined') {
    return clientApiKey
  }
  const session = localStorage.getItem(EMAIL_SESSION_KEY)?.trim()
  return session || clientApiKey
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 seconds for AI generation
})

apiClient.interceptors.request.use((config) => {
  const token = bearerForRequests()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  } else {
    delete config.headers.Authorization
  }
  return config
})

/**
 * Quick check that the backend is reachable.
 * Uses `fetch` (not axios) so the probe does not send JSON / optional API-key headers.
 * Without `VITE_API_BASE_URL`, calls same-origin `/api/health` so the Vite dev proxy forwards to :8000.
 */
/** Public hints from GET /auth/email/config (no secrets). */
export type AuthEmailConfig = {
  require_email_login: boolean
  email_backend: 'smtp' | 'resend'
  dev_inbox_url: string | null
}

const defaultAuthEmailConfig: AuthEmailConfig = {
  require_email_login: false,
  email_backend: 'smtp',
  dev_inbox_url: null,
}

/** When config cannot be loaded, assume login is required in production builds (fail closed). */
function authConfigFallback(): AuthEmailConfig {
  const force =
    import.meta.env.PROD === true || import.meta.env.VITE_REQUIRE_EMAIL_LOGIN === 'true'
  if (force && import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL?.trim()) {
    console.warn(
      '[Ghostwriter] Auth config could not be loaded. Set VITE_API_BASE_URL to your backend URL ' +
        '(Railway frontend Variables, then rebuild) so /auth/email and /generate reach the API.',
    )
  }
  return {
    ...defaultAuthEmailConfig,
    require_email_login: force,
  }
}

export async function fetchAuthEmailConfig(): Promise<AuthEmailConfig> {
  try {
    const direct = import.meta.env.VITE_API_BASE_URL?.trim()
    const url = direct
      ? `${direct.replace(/\/$/, '')}/auth/email/config`
      : '/api/auth/email/config'
    const r = await fetch(url, { cache: 'no-store' })
    if (!r.ok) {
      return authConfigFallback()
    }
    const ct = r.headers.get('content-type') || ''
    if (!ct.includes('application/json')) {
      return authConfigFallback()
    }
    const data = (await r.json()) as Partial<AuthEmailConfig>
    return {
      require_email_login: Boolean(data.require_email_login),
      email_backend: data.email_backend === 'resend' ? 'resend' : 'smtp',
      dev_inbox_url: typeof data.dev_inbox_url === 'string' ? data.dev_inbox_url : null,
    }
  } catch {
    return authConfigFallback()
  }
}

export function clearEmailSession(): void {
  if (typeof localStorage === 'undefined') return
  localStorage.removeItem(EMAIL_SESSION_KEY)
}

export async function sendEmailVerificationCode(email: string): Promise<void> {
  try {
    await apiClient.post('/auth/email/send-code', { email })
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail?: string }>
      const message =
        axiosError.response?.data?.detail ||
        axiosError.message ||
        'Could not send verification code'
      throw new Error(message)
    }
    throw error
  }
}

export async function verifyEmailCode(
  email: string,
  code: string
): Promise<{ access_token: string; expires_in: number }> {
  try {
    const response = await apiClient.post<{ access_token: string; expires_in: number }>(
      '/auth/email/verify',
      { email, code }
    )
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail?: string }>
      const message =
        axiosError.response?.data?.detail ||
        axiosError.message ||
        'Verification failed'
      throw new Error(message)
    }
    throw error
  }
}

export async function logoutEmailSession(): Promise<void> {
  try {
    await apiClient.post('/auth/email/logout')
  } finally {
    clearEmailSession()
  }
}

export async function fetchBackendHealth(): Promise<boolean> {
  try {
    const direct = import.meta.env.VITE_API_BASE_URL?.trim()
    const url = direct ? `${direct.replace(/\/$/, '')}/health` : '/api/health'

    const ctrl = new AbortController()
    const tid = setTimeout(() => ctrl.abort(), 5000)
    let r: Response
    try {
      r = await fetch(url, {
        method: 'GET',
        cache: 'no-store',
        signal: ctrl.signal,
      })
    } finally {
      clearTimeout(tid)
    }
    if (!r.ok) return false
    const data = (await r.json()) as { status?: string }
    return data?.status === 'healthy'
  } catch {
    return false
  }
}

export async function generateContent(request: GenerateRequest): Promise<GenerateResponse> {
  try {
    const response = await apiClient.post<GenerateResponse>('/generate', request)
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail?: string }>
      let message =
        axiosError.response?.data?.detail || axiosError.message || 'Failed to generate content'
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
  const streamParams = new URLSearchParams({
    data: JSON.stringify(request),
  })
  const streamToken = bearerForRequests()
  if (streamToken) {
    streamParams.set('api_key', streamToken)
  }
  const eventSource = new EventSource(
    `${API_BASE_URL}/generate/stream?${streamParams}`
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
