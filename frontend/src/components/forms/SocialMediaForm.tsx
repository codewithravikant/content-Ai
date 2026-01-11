import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { socialMediaSchema, SocialMediaFormData, normalizeWordCount } from '../../forms/schema'
import { generateContent } from '../../services/api'
import { useEffect } from 'react'
import { Sparkles } from 'lucide-react'

interface SocialMediaFormProps {
  onGenerate: (content: string) => void
  onGenerateStart: () => void
  onError: (error: string) => void
}

const STORAGE_KEY = 'content_ai_social_media_form'

export function SocialMediaForm({ onGenerate, onGenerateStart, onError }: SocialMediaFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
  } = useForm<SocialMediaFormData>({
    resolver: zodResolver(socialMediaSchema),
    defaultValues: {
      platform: 'twitter',
      topic: '',
      tone: 'engaging',
      goal: '',
      hashtag_count: 3,
      word_count: '50-300',
    },
  })

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        Object.keys(data).forEach((key) => {
          setValue(key as keyof SocialMediaFormData, data[key])
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

  const onSubmit = async (data: SocialMediaFormData) => {
    try {
      onGenerateStart()
      const wordTarget = normalizeWordCount(data.word_count || '50-300')
      const response = await generateContent({
        content_type: 'social_media',
        context: {
          platform: data.platform,
          topic: data.topic,
          tone: data.tone,
          goal: data.goal || 'Engage audience',
        },
        specifications: {
          hashtag_count: data.hashtag_count || 3,
          word_target: wordTarget,
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
          Platform *
        </label>
        <select 
          {...register('platform')}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all text-slate-100"
        >
          <option value="twitter">Twitter/X</option>
          <option value="x">X (formerly Twitter)</option>
          <option value="instagram">Instagram</option>
          <option value="linkedin">LinkedIn</option>
          <option value="facebook">Facebook</option>
        </select>
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Topic *
        </label>
        <textarea 
          {...register('topic')}
          placeholder="What should the post be about?"
          rows={3}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all resize-none placeholder:text-slate-600 text-slate-100"
        />
        {errors.topic && (
          <p className="text-xs text-red-400 mt-1">{errors.topic.message}</p>
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
          Goal (Optional)
        </label>
        <input 
          {...register('goal')}
          placeholder="e.g., Drive engagement, Promote product, Share insight"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Hashtag Count (0-20)
        </label>
        <input 
          type="number"
          {...register('hashtag_count', { valueAsNumber: true })}
          min={0}
          max={20}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all text-slate-100"
        />
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Word Count (min-max) - Min: 50
        </label>
        <input 
          {...register('word_count')}
          placeholder="e.g., 50-300"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="group relative w-full overflow-hidden rounded-2xl py-5 transition-all duration-300 active:scale-[0.98] disabled:opacity-50"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-600 animate-gradient-x"></div>
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
              Generate Social Media Post
            </>
          )}
        </span>
      </button>
    </form>
  )
}
