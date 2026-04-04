import { useState } from 'react'
import { ExternalLink, Loader2, Mail, ShieldCheck } from 'lucide-react'
import {
  sendEmailVerificationCode,
  verifyEmailCode,
  EMAIL_SESSION_KEY,
  type AuthEmailConfig,
} from '../services/api'

type LoginModalProps = {
  onVerified: () => void
  emailDelivery: Pick<AuthEmailConfig, 'email_backend' | 'dev_inbox_url'>
}

export function LoginModal({ onVerified, emailDelivery }: LoginModalProps) {
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [step, setStep] = useState<'email' | 'code'>('email')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const { email_backend: backend, dev_inbox_url: devInboxUrl } = emailDelivery

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await sendEmailVerificationCode(email.trim())
      setStep('code')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send the verification code.')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const digits = code.replace(/\D/g, '').slice(0, 6)
      const { access_token } = await verifyEmailCode(email.trim(), digits)
      localStorage.setItem(EMAIL_SESSION_KEY, access_token)
      onVerified()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'That code is invalid or expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-modal-title"
      aria-describedby="login-modal-desc"
    >
      <div className="w-full max-w-[420px] overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-[#0f172a] to-[#0b0f1a] shadow-2xl shadow-black/50">
        <div className="border-b border-white/5 bg-white/[0.03] px-8 py-6">
          <div className="flex items-start gap-4">
            <div className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-indigo-600 text-white shadow-lg shadow-cyan-500/20">
              <ShieldCheck size={22} strokeWidth={2.25} />
            </div>
            <div className="min-w-0 flex-1">
              <h2
                id="login-modal-title"
                className="text-lg font-semibold tracking-tight text-white sm:text-xl"
              >
                Sign in
              </h2>
              <p id="login-modal-desc" className="mt-1 text-sm leading-relaxed text-slate-400">
                We’ll send a one-time verification code to your email. No password required.
              </p>
            </div>
          </div>
          <div className="mt-5 flex gap-2">
            <div
              className={`h-1 flex-1 rounded-full ${step === 'email' ? 'bg-cyan-500' : 'bg-slate-700'}`}
              aria-hidden
            />
            <div
              className={`h-1 flex-1 rounded-full ${step === 'code' ? 'bg-cyan-500' : 'bg-slate-700'}`}
              aria-hidden
            />
          </div>
          <p className="mt-2 text-center text-[10px] font-medium uppercase tracking-widest text-slate-600">
            {step === 'email' ? 'Step 1 of 2 — Your email' : 'Step 2 of 2 — Enter code'}
          </p>
        </div>

        <div className="px-8 py-7">
          {step === 'email' ? (
            <form onSubmit={handleSendCode} className="space-y-5">
              <div>
                <label
                  htmlFor="gw-login-email"
                  className="mb-2 block text-xs font-medium text-slate-300"
                >
                  Work email
                </label>
                <input
                  id="gw-login-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/25"
                  placeholder="name@company.com"
                />
              </div>

              {backend === 'smtp' && devInboxUrl ? (
                <div className="rounded-xl border border-amber-500/20 bg-amber-950/30 px-4 py-3 text-xs leading-relaxed text-amber-100/90">
                  <strong className="font-semibold text-amber-200">Local development</strong>
                  <p className="mt-1.5 text-amber-100/80">
                    Mail is sent to a local catcher (not the real internet). After you click Send
                    code, open{' '}
                    <a
                      href={devInboxUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-cyan-300 underline decoration-cyan-500/40 underline-offset-2 hover:text-cyan-200"
                    >
                      the mail inbox
                    </a>{' '}
                    to copy the 6-digit code. If nothing arrives, run{' '}
                    <code className="rounded bg-black/30 px-1.5 py-0.5 font-mono text-[11px] text-amber-200">
                      make mailpit
                    </code>{' '}
                    in another terminal.
                  </p>
                </div>
              ) : backend === 'resend' ? (
                <div className="rounded-xl border border-slate-600/30 bg-slate-800/40 px-4 py-3 text-xs leading-relaxed text-slate-300">
                  <strong className="font-semibold text-slate-200">Resend</strong>
                  <p className="mt-1.5">
                    The code is sent by Resend to your real inbox. Check spam if you do not see it
                    within a minute.
                  </p>
                  <p className="mt-2 text-slate-500">
                    Hosting this app? Create a free account at{' '}
                    <a
                      href="https://resend.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-cyan-400/90 underline decoration-cyan-500/30 underline-offset-2 hover:text-cyan-300"
                    >
                      resend.com
                    </a>{' '}
                    and set <code className="rounded bg-black/25 px-1 font-mono text-[11px]">RESEND_API_KEY</code>{' '}
                    (and <code className="rounded bg-black/25 px-1 font-mono text-[11px]">RESEND_FROM</code>) in
                    your server environment (e.g. Railway Variables).
                  </p>
                </div>
              ) : (
                <div className="rounded-xl border border-slate-600/30 bg-slate-800/40 px-4 py-3 text-xs text-slate-400">
                  Verification email is sent via your configured SMTP server.
                </div>
              )}

              {error && (
                <div
                  className="rounded-xl border border-rose-500/25 bg-rose-950/40 px-4 py-3 text-sm text-rose-100"
                  role="alert"
                >
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3.5 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/15 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? <Loader2 className="animate-spin" size={18} aria-hidden /> : null}
                Send verification code
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerify} className="space-y-5">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Mail size={16} className="shrink-0 text-slate-500" aria-hidden />
                <span>
                  Code sent to{' '}
                  <span className="font-medium text-slate-200">{email}</span>
                </span>
              </div>

              {backend === 'smtp' && devInboxUrl && (
                <a
                  href={devInboxUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-cyan-300 transition hover:bg-white/10 hover:text-cyan-200"
                >
                  <ExternalLink size={16} />
                  Open mail inbox
                </a>
              )}

              {backend === 'resend' && (
                <p className="text-xs leading-relaxed text-slate-500">
                  Check your inbox and spam folder. The code expires in about 10 minutes. Delivery uses{' '}
                  <a
                    href="https://resend.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-500/90 underline decoration-cyan-500/25 underline-offset-2 hover:text-cyan-400"
                  >
                    Resend
                  </a>
                  ; the server must have a valid API key configured.
                </p>
              )}

              <div>
                <label
                  htmlFor="gw-login-code"
                  className="mb-2 block text-xs font-medium text-slate-300"
                >
                  6-digit code
                </label>
                <input
                  id="gw-login-code"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={8}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full rounded-xl border border-white/10 bg-slate-900/80 px-4 py-3 text-center font-mono text-2xl tracking-[0.35em] text-slate-100 outline-none transition focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/25"
                  placeholder="••••••"
                  autoFocus
                />
              </div>

              {error && (
                <div
                  className="rounded-xl border border-rose-500/25 bg-rose-950/40 px-4 py-3 text-sm text-rose-100"
                  role="alert"
                >
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setStep('email')
                    setCode('')
                    setError(null)
                  }}
                  className="flex-1 rounded-xl border border-white/10 px-4 py-3.5 text-sm font-medium text-slate-300 transition hover:bg-white/5"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3.5 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/15 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading ? <Loader2 className="animate-spin" size={18} aria-hidden /> : null}
                  Verify & continue
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
