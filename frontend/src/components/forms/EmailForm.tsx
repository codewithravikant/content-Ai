import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { emailSchema, EmailFormData } from '../../forms/schema'
import { generateContent } from '../../services/api'
import { useEffect } from 'react'
import { Sparkles } from 'lucide-react'

interface EmailFormProps {
  onGenerate: (content: string) => void
  onGenerateStart: () => void
  onError: (error: string) => void
}

const STORAGE_KEY = 'ghostwriter_email_form'

export function EmailForm({ onGenerate, onGenerateStart, onError }: EmailFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
  } = useForm<EmailFormData>({
    resolver: zodResolver(emailSchema),
    defaultValues: {
      purpose: '',
      recipient_context: '',
      key_points: '',
      tone: 'professional',
      urgency_level: 'medium',
      cta: '',
    },
  })

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        Object.keys(data).forEach((key) => {
          setValue(key as keyof EmailFormData, data[key])
        })
      } catch (e) {
        console.error('Failed to load form data:', e)
      }
    }
  }, [setValue])

  const formData = watch()
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(formData))
    }, 500)
    return () => clearTimeout(timeoutId)
  }, [formData])

  const onSubmit = async (data: EmailFormData) => {
    try {
      onGenerateStart()
      const response = await generateContent({
        content_type: 'email',
        context: {
          purpose: data.purpose,
          recipient_context: data.recipient_context,
          key_points: data.key_points,
          tone: data.tone,
        },
        specifications: {
          urgency_level: data.urgency_level,
          cta: data.cta || undefined,
        },
      })
      onGenerate(response.content)
    } catch (error: any) {
      onError(error.message || 'Failed to generate content')
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Purpose *
        </label>
        <input 
          {...register('purpose')}
          placeholder="e.g., Follow-up on meeting, Request for feedback"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
        {errors.purpose && (
          <p className="text-xs text-red-400 mt-1">{errors.purpose.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Recipient Context *
        </label>
        <textarea 
          {...register('recipient_context')}
          placeholder="e.g., Client we met last week, Internal team member"
          rows={3}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all resize-none placeholder:text-slate-600 text-slate-100"
        />
        {errors.recipient_context && (
          <p className="text-xs text-red-400 mt-1">{errors.recipient_context.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Key Points *
        </label>
        <textarea 
          {...register('key_points')}
          placeholder="List the main points you want to convey"
          rows={5}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all resize-none placeholder:text-slate-600 text-slate-100"
        />
        {errors.key_points && (
          <p className="text-xs text-red-400 mt-1">{errors.key_points.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Tone *
        </label>
        <select 
          {...register('tone')}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all text-slate-100"
        >
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="friendly">Friendly</option>
          <option value="formal">Formal</option>
          <option value="engaging">Engaging</option>
          <option value="persuasive">Persuasive</option>
        </select>
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Urgency Level
        </label>
        <select 
          {...register('urgency_level')}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all text-slate-100"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Call to Action (Optional)
        </label>
        <input 
          {...register('cta')}
          placeholder="e.g., Please respond by Friday, Schedule a call"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="group relative w-full overflow-hidden rounded-2xl py-5 transition-all duration-300 active:scale-[0.98] disabled:opacity-50"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-indigo-500 to-violet-600 animate-gradient-x"></div>
        <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors"></div>
        <span className="relative flex items-center justify-center gap-3 text-white font-black text-sm uppercase tracking-[0.2em]">
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles size={18} className="group-hover:rotate-12 transition-transform" />
              Generate Email
            </>
          )}
        </span>
      </button>
    </form>
  )
}
