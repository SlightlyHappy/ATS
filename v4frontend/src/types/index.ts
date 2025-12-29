// User and Authentication Types
export interface User {
  id: string
  email: string
  username: string
  is_admin: boolean
  is_active: boolean
  credits_balance: number
  created_at: string
  last_login?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface LoginForm {
  email: string
  password: string
}

export interface RegisterForm {
  email: string
  password: string
  username: string
}

// Resume Types
export interface Resume {
  id: string
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  processing_status: 'pending' | 'text_extracted' | 'failed'
  batch_upload_id?: string
  created_at: string
  processed_at?: string
  analyses_count: number
  structured_data?: {
    contact_info?: {
      name?: string
      email?: string
      phone?: string
    }
    sections?: {
      experience?: string
      education?: string
      skills?: string
    }
  }
}

// Analysis Types
export interface Analysis {
  id: string
  resume_id: string
  analysis_type: string
  overall_score: number
  scores_breakdown: {
    technical_skills: ScoreDetail
    experience: ScoreDetail
    education: ScoreDetail
    soft_skills: ScoreDetail
  }
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  processing_time: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
  agent_results?: AgentResults
}

export interface ScoreDetail {
  score: number
  confidence: number
  weight: number
}

export interface AgentResults {
  technical_skills?: TechnicalSkillsAgent
  experience?: ExperienceAgent
  education?: EducationAgent
  soft_skills?: SoftSkillsAgent
}

export interface TechnicalSkillsAgent {
  industry_classification: {
    primary_industry: string
    secondary_industries: string[]
    industry_expertise_level: string
  }
  technical_skills: {
    programming_languages: Array<{
      name: string
      proficiency: string
      years_experience: number
      industry_context: string
      indian_demand: string
    }>
    platforms_systems: Array<{
      name: string
      services: string[]
      certification_level: string
    }>
  }
  skill_assessment: {
    technical_depth_score: number
    technical_breadth_score: number
    indian_market_relevance: number
    skill_currency: number
  }
}

export interface ExperienceAgent {
  career_overview: {
    total_experience: string
    relevant_experience: string
    primary_industry: string
    industry_diversity: string[]
    career_level: string
  }
  work_experience: Array<{
    company: string
    role: string
    duration: string
    company_type: string
    industry: string
    achievements: string[]
    impact_score: number
    leadership_scope: string
  }>
  leadership_assessment: {
    people_management: {
      direct_reports: number[]
      team_sizes_led: number[]
      leadership_style: string
    }
  }
}

export interface EducationAgent {
  education_overview: {
    highest_qualification: string
    primary_field: string
    education_level_score: number
    institution_prestige_score: number
  }
  formal_education: Array<{
    degree: string
    field: string
    institution: string
    year: number
    grade: string
    indian_context: {
      institution_tier: string
      entrance_exam: string
    }
  }>
}

export interface SoftSkillsAgent {
  soft_skills_overview: {
    overall_soft_skills_score: number
    cultural_fit_score: number
    interpersonal_effectiveness: number
    leadership_potential: number
  }
  communication_skills: {
    verbal_communication: {
      clarity_of_expression: number
      public_speaking: string
      multilingual_ability: string[]
    }
  }
  indian_workplace_fit: {
    hierarchical_navigation: {
      respect_for_authority: string
      chain_of_command: string
      score: number
    }
    cultural_adaptation: {
      festival_awareness: string
      regional_sensitivity: string
      score: number
    }
  }
}

// Queue Types
export interface QueueItem {
  id: string
  resume_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  priority: number
  queue_position: number
  estimated_completion_time: string
  created_at: string
}

export interface QueueStats {
  total_pending: number
  total_processing: number
  average_wait_time: string
  estimated_completion: string
}

export interface BatchUpload {
  id: string
  batch_name: string
  total_resumes: number
  processed_resumes: number
  successful_analyses: number
  failed_analyses: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  credits_used: number
  created_at: string
  completed_at?: string
}

// Credit Types
export interface CreditTransaction {
  id: string
  transaction_type: 'credit' | 'debit'
  amount: number
  description: string
  balance_after: number
  created_at: string
}

export interface CreditInfo {
  user_id: string
  credits_balance: number
  total_credits_purchased: number
  total_credits_used: number
  is_admin: boolean
  recent_transactions: CreditTransaction[]
}

// Admin Types
export interface AdminUser extends User {
  admin_profile: {
    role: string
    access_level: number
    is_active: boolean
    login_count: number
    actions_performed: number
    failed_login_attempts: number
    last_login_ip: string
    created_at: string
  }
}

export interface SystemConfig {
  id: string
  key: string
  value: any
  category: string
  description: string
  is_sensitive: boolean
  requires_restart: boolean
  created_at: string
}

export interface AdminAnalytics {
  summary: {
    total_users: number
    new_users: number
    active_users: number
    total_resumes: number
    completed_analyses: number
    pending_analyses: number
    total_credits_used: number
    avg_credits_per_user: number
  }
  daily_stats: Array<{
    date: string
    new_users: number
    uploads: number
    analyses: number
    credits_used: number
  }>
  queue_health: {
    status: string
    average_wait_time: number
    max_queue_length: number
    processing_rate: number
  }
  generated_at: string
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'queue_update' | 'analysis_complete' | 'notification' | 'system_alert'
  data: any
  timestamp: string
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T
  message?: string
  error?: string
  pagination?: {
    page: number
    per_page: number
    total: number
    pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export interface ApiError {
  error: string
  details?: string
  code?: string
  timestamp: string
  request_id?: string
  validation_errors?: Array<{
    field: string
    message: string
  }>
}
