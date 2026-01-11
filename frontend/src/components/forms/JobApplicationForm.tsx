import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { jobApplicationSchema, JobApplicationFormData, normalizeWordCount } from '../../forms/schema'
import { generateContent } from '../../services/api'
import { useEffect } from 'react'
import { Sparkles } from 'lucide-react'

interface JobApplicationFormProps {
  onGenerate: (content: string) => void
  onGenerateStart: () => void
  onError: (error: string) => void
}

const STORAGE_KEY = 'ghostwriter_job_application_form'

export function JobApplicationForm({ onGenerate, onGenerateStart, onError }: JobApplicationFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
  } = useForm<JobApplicationFormData>({
    resolver: zodResolver(jobApplicationSchema),
    defaultValues: {
      position_title: '',
      company_name: '',
      key_qualifications: '',
      experience_level: 'intermediate',
      application_type: 'cover_letter',
      word_count: '300-500',
    },
  })

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        Object.keys(data).forEach((key) => {
          setValue(key as keyof JobApplicationFormData, data[key])
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

  const onSubmit = async (data: JobApplicationFormData) => {
    try {
      onGenerateStart()
      const wordTarget = normalizeWordCount(data.word_count || '300-500')
      const response = await generateContent({
        content_type: 'job_application',
        context: {
          position_title: data.position_title,
          company_name: data.company_name,
          key_qualifications: data.key_qualifications,
          experience_level: data.experience_level,
        },
        specifications: {
          application_type: data.application_type || 'cover_letter',
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
          Position Title *
        </label>
        <input 
          {...register('position_title')}
          placeholder="e.g., Senior Software Engineer, Product Manager"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
        {errors.position_title && (
          <p className="text-xs text-red-400 mt-1">{errors.position_title.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Company Name *
        </label>
        <input 
          {...register('company_name')}
          placeholder="e.g., Google, Microsoft, Startup Inc"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
        {errors.company_name && (
          <p className="text-xs text-red-400 mt-1">{errors.company_name.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Key Qualifications *
        </label>
        <textarea 
          {...register('key_qualifications')}
          placeholder="List your key qualifications, skills, and relevant experience"
          rows={6}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all resize-none placeholder:text-slate-600 text-slate-100"
        />
        {errors.key_qualifications && (
          <p className="text-xs text-red-400 mt-1">{errors.key_qualifications.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Experience Level *
        </label>
        <select 
          {...register('experience_level')}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all text-slate-100"
        >
          <option value="entry-level">Entry Level</option>
          <option value="mid-level">Mid Level</option>
          <option value="senior">Senior</option>
          <option value="executive">Executive</option>
        </select>
        {errors.experience_level && (
          <p className="text-xs text-red-400 mt-1">{errors.experience_level.message}</p>
        )}
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Application Type
        </label>
        <select 
          {...register('application_type')}
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all text-slate-100"
        >
          <option value="cover_letter">Cover Letter</option>
          <option value="application_letter">Application Letter</option>
        </select>
      </div>

      <div className="relative">
        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 block">
          Word Count (min-max) - Min: 50
        </label>
        <input 
          {...register('word_count')}
          placeholder="e.g., 300-500"
          className="w-full bg-white/5 border border-white/10 p-4 rounded-xl text-sm focus:border-cyan-500/50 focus:bg-white/10 outline-none transition-all placeholder:text-slate-600 text-slate-100"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="group relative w-full overflow-hidden rounded-2xl py-5 transition-all duration-300 active:scale-[0.98] disabled:opacity-50"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-600 animate-gradient-x"></div>
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
              Generate Job Application
            </>
          )}
        </span>
      </button>
    </form>
  )
}
