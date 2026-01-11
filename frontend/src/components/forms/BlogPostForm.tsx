import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { blogPostSchema, BlogPostFormData, normalizeWordCount } from '../../forms/schema'
import { generateContent } from '../../services/api'
import { useEffect } from 'react'
import { Sparkles } from 'lucide-react'

interface BlogPostFormProps {
  onGenerate: (content: string) => void
  onGenerateStart: () => void
  onError: (error: string) => void
}

const STORAGE_KEY = 'content_ai_blog_post_form'

export function BlogPostForm({ onGenerate, onGenerateStart, onError }: BlogPostFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
  } = useForm<BlogPostFormData>({
    resolver: zodResolver(blogPostSchema),
    defaultValues: {
      topic: '',
      target_audience: '',
      word_count: '100-300',
      tone: 'engaging',
      seo_focus: false,
      expertise_level: 'beginner',
    },
  })

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        Object.keys(data).forEach((key) => {
          setValue(key as keyof BlogPostFormData, data[key])
        })
      } catch (e) {
        console.error('Failed to load form data:', e)
      }
    }
  }, [setValue])

  // Save to localStorage on change
  const formData = watch()
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(formData))
    }, 500)
    return () => clearTimeout(timeoutId)
  }, [formData])

  const onSubmit = async (data: BlogPostFormData) => {
    try {
      onGenerateStart()
      const wordTarget = normalizeWordCount(data.word_count)
      const response = await generateContent({
        content_type: 'blog_post',
        context: {
          topic: data.topic,
          audience: data.target_audience,
          tone: data.tone,
        },
        specifications: {
          word_target: wordTarget,
          seo_enabled: data.seo_focus,
          expertise: data.expertise_level,
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
        <input 
          {...register('topic')}
          placeholder="e.g., Introduction to Machine Learning"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
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
          placeholder="e.g., General public, Students, Professionals"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
        {errors.target_audience && (
          <p className="text-xs text-red-400 mt-1">{errors.target_audience.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Word Count (min-max) * - Min: 50
        </label>
        <input 
          {...register('word_count')}
          placeholder="e.g., 50-300"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
        {errors.word_count && (
          <p className="text-xs text-red-400 mt-1">{errors.word_count.message}</p>
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
        {errors.tone && (
          <p className="text-xs text-red-400 mt-1">{errors.tone.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Expertise Level
        </label>
        <select 
          {...register('expertise_level')}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all text-slate-100"
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
      </div>

      <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/5">
        <input 
          type="checkbox" 
          {...register('seo_focus')}
          className="w-4 h-4 rounded border-white/10 bg-white/5 text-cyan-500 focus:ring-cyan-500/50"
        />
        <label className="text-sm text-slate-300">SEO Focus</label>
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
              Generate Blog Post
            </>
          )}
        </span>
      </button>
    </form>
  )
}
