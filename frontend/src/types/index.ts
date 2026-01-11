export type ContentType = 'blog_post' | 'email' | 'social_media' | 'linkedin' | 'job_application'

export type Tone = 'professional' | 'casual' | 'friendly' | 'formal' | 'engaging' | 'persuasive'

export type ExpertiseLevel = 'beginner' | 'intermediate' | 'advanced'

export interface BlogPostInput {
  topic: string
  target_audience: string
  word_count: string // e.g., "800-1000"
  tone: Tone
  seo_focus?: boolean
  expertise_level?: ExpertiseLevel
}

export interface EmailInput {
  purpose: string
  recipient_context: string
  key_points: string
  tone: Tone
  urgency_level?: 'low' | 'medium' | 'high'
  cta?: string
}

export interface GenerateRequest {
  content_type: ContentType
  context: Record<string, any>
  specifications: Record<string, any>
  generation_params?: {
    temperature?: number
    max_tokens?: number
    top_p?: number
  }
}

export interface GenerateResponse {
  content: string
  metadata?: {
    word_count?: number
    sections?: string[]
    tokens_used?: number
    hashtags?: string[]
    estimated_read_time?: string
    seo_keywords?: string[]
  }
}
