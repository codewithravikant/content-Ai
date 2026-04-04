/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  /** Optional shared secret when backend sets GHOSTWRITER_CLIENT_API_KEY (visible in browser; use a gateway for real protection). */
  readonly VITE_CLIENT_API_KEY?: string
}
