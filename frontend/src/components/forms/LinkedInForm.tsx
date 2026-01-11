import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { linkedinSchema, LinkedInFormData, normalizeWordCount } from '../../forms/schema'
import { generateContent } from '../../services/api'
import { useEffect } from 'react'
import { Sparkles } from 'lucide-react'

interface LinkedInFormProps {
  onGenerate: (content: string) => void
  onGenerateStart: () => void
  onError: (error: string) => void
}

const STORAGE_KEY = 'content_ai_linkedin_form'

export function LinkedInForm({ onGenerate, onGenerateStart, onError }: LinkedInFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
  } = useForm<LinkedInFormData>({
    resolver: zodResolver(linkedinSchema),
    defaultValues: {
      topic: '',
      target_audience: '',
      engagement_goal: '',
      tone: 'professional',
      word_count: '200-400',
      include_hashtags: true,
    },
  })

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        Object.keys(data).forEach((key) => {
          setValue(key as keyof LinkedInFormData, data[key])
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

  const onSubmit = async (data: LinkedInFormData) => {
    try {
      onGenerateStart()
      const wordTarget = normalizeWordCount(data.word_count || '200-400')
      const response = await generateContent({
        content_type: 'linkedin',
        context: {
          topic: data.topic,
          target_audience: data.target_audience,
          engagement_goal: data.engagement_goal || 'Share insights and engage network',
          tone: data.tone,
        },
        specifications: {
          word_target: wordTarget,
          include_hashtags: data.include_hashtags ?? true,
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
          Topic *
        </label>
        <textarea 
          {...register('topic')}
          placeholder="What should your LinkedIn post be about?"
          rows={3}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all resize-none placeholder:text-slate-600 text-slate-100"
        />
        {errors.topic && (
          <p className="text-xs text-red-400 mt-1">{errors.topic.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Target Audience *
        </label>
        <input 
          {...register('target_audience')}
          placeholder="e.g., Tech professionals, Entrepreneurs, Industry leaders"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
        {errors.target_audience && (
          <p className="text-xs text-red-400 mt-1">{errors.target_audience.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Engagement Goal (Optional)
        </label>
        <input 
          {...register('engagement_goal')}
          placeholder="e.g., Generate discussion, Share insights, Build connections"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
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
          Word Count (min-max) - Min: 50
        </label>
        <input 
          {...register('word_count')}
          placeholder="e.g., 200-400"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
      </div>

      <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/5">
        <input 
          type="checkbox" 
          {...register('include_hashtags')}
          className="w-4 h-4 rounded border-white/10 bg-white/5 text-cyan-500 focus:ring-cyan-500/50"
        />
        <label className="text-sm text-slate-300">Include Hashtags</label>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="group relative w-full overflow-hidden rounded-2xl py-5 transition-all duration-300 active:scale-[0.98] disabled:opacity-50"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 animate-gradient-x"></div>
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
              Generate LinkedIn Post
            </>
          )}
        </span>
      </button>
    </form>
  )
}
