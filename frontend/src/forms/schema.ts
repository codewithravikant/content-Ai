import { z } from 'zod'

export const blogPostSchema = z.object({
  topic: z.string().min(3, 'Topic must be at least 3 characters').max(200, 'Topic must be less than 200 characters'),
  target_audience: z.string().min(3, 'Target audience must be at least 3 characters').max(100),
  word_count: z.string().regex(/^\d+-\d+$/, 'Word count must be in format "min-max" (e.g., "50-300")').refine(
    (val) => {
      const match = val.match(/^(\d+)-(\d+)$/)
      if (!match) return false
      const min = parseInt(match[1], 10)
      return min >= 50
    },
    { message: 'Minimum word count must be at least 50' }
  ),
  tone: z.enum(['professional', 'casual', 'friendly', 'formal', 'engaging', 'persuasive'], {
    errorMap: () => ({ message: 'Please select a valid tone' }),
  }),
  seo_focus: z.boolean().optional().default(false),
  expertise_level: z.enum(['beginner', 'intermediate', 'advanced']).optional().default('beginner'),
})

export const emailSchema = z.object({
  purpose: z.string().min(5, 'Purpose must be at least 5 characters').max(200),
  recipient_context: z.string().min(5, 'Recipient context must be at least 5 characters').max(500),
  key_points: z.string().min(10, 'Key points must be at least 10 characters').max(1000),
  tone: z.enum(['professional', 'casual', 'friendly', 'formal', 'engaging', 'persuasive'], {
    errorMap: () => ({ message: 'Please select a valid tone' }),
  }),
  urgency_level: z.enum(['low', 'medium', 'high']).optional().default('medium'),
  cta: z.string().max(100).optional(),
})

export type BlogPostFormData = z.infer<typeof blogPostSchema>
export type EmailFormData = z.infer<typeof emailSchema>

// Normalization utilities
export function normalizeWordCount(wordCount: string): number {
  const match = wordCount.match(/^(\d+)-(\d+)$/)
  if (!match) return 50 // default minimum
  const min = parseInt(match[1], 10)
  const max = parseInt(match[2], 10)
  if (min < 50 || max < 50 || min > max) return 50
  const result = Math.floor((min + max) / 2)
  return Math.max(50, result) // Ensure minimum 50
}

// New content type schemas
export const socialMediaSchema = z.object({
  platform: z.string().min(2, 'Platform must be at least 2 characters').max(50),
  topic: z.string().min(3, 'Topic must be at least 3 characters').max(500),
  tone: z.enum(['professional', 'casual', 'friendly', 'formal', 'engaging', 'persuasive'], {
    errorMap: () => ({ message: 'Please select a valid tone' }),
  }),
  goal: z.string().max(200).optional(),
  hashtag_count: z.number().min(0).max(20).optional().default(3),
  word_count: z.string()
    .regex(/^\d+-\d+$/, 'Word count must be in format "min-max"')
    .refine(
      (val) => {
        const match = val.match(/^(\d+)-(\d+)$/)
        if (!match) return false
        const min = parseInt(match[1], 10)
        return min >= 50
      },
      { message: 'Minimum word count must be at least 50' }
    )
    .optional()
    .default('50-300'),
})

export const linkedinSchema = z.object({
  topic: z.string().min(3, 'Topic must be at least 3 characters').max(500),
  target_audience: z.string().min(3, 'Target audience must be at least 3 characters').max(200),
  engagement_goal: z.string().max(200).optional(),
  tone: z.enum(['professional', 'casual', 'friendly', 'formal', 'engaging', 'persuasive'], {
    errorMap: () => ({ message: 'Please select a valid tone' }),
  }),
  word_count: z.string()
    .regex(/^\d+-\d+$/, 'Word count must be in format "min-max"')
    .refine(
      (val) => {
        const match = val.match(/^(\d+)-(\d+)$/)
        if (!match) return false
        const min = parseInt(match[1], 10)
        return min >= 50
      },
      { message: 'Minimum word count must be at least 50' }
    )
    .optional()
    .default('200-400'),
  include_hashtags: z.boolean().optional().default(true),
})

export const jobApplicationSchema = z.object({
  position_title: z.string().min(3, 'Position title must be at least 3 characters').max(200),
  company_name: z.string().min(2, 'Company name must be at least 2 characters').max(200),
  key_qualifications: z.string().min(10, 'Key qualifications must be at least 10 characters').max(1000),
  experience_level: z.string().min(3, 'Experience level must be at least 3 characters').max(50),
  application_type: z.string().max(50).optional().default('cover_letter'),
  word_count: z.string()
    .regex(/^\d+-\d+$/, 'Word count must be in format "min-max"')
    .refine(
      (val) => {
        const match = val.match(/^(\d+)-(\d+)$/)
        if (!match) return false
        const min = parseInt(match[1], 10)
        return min >= 50
      },
      { message: 'Minimum word count must be at least 50' }
    )
    .optional()
    .default('300-500'),
})

export type SocialMediaFormData = z.infer<typeof socialMediaSchema>
export type LinkedInFormData = z.infer<typeof linkedinSchema>
export type JobApplicationFormData = z.infer<typeof jobApplicationSchema>

export function normalizeTone(tone: string): string {
  return tone.toLowerCase().trim()
}
