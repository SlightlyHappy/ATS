export type User = {
  // Original frontend fields
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: 'Admin' | 'Member' | 'Guest';
  plan: 'Free' | 'Pro' | 'Enterprise';
  lastSeen: string;
  // New API fields
  user_id?: string;
  access_type?: 'admin' | 'user';
  is_trial?: boolean;
  trial_info?: {
    resume_limit: number;
    legal_limit: number;
    used_resumes: number;
    used_legal: number;
  };
  created_at?: string;
  last_login?: string;
  // User status fields for soft delete support
  status?: 'active' | 'inactive' | 'deactivated';
  active?: boolean;
  is_active?: boolean;
};

export type ResumeStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type Resume = {
  // Core upload fields
  id: string;
  user_id: string;
  filename: string;
  file_url: string;
  upload_date: string;
  status: string; // Initially "uploaded"
  
  // Analysis results fields
  overall_score?: number;
  experience_score?: number;
  skills_score?: number;
  education_score?: number;
  
  // Candidate information
  candidate_name?: string;
  candidate_email?: string;
  candidate_phone?: string;
  
  // Analysis content
  summary?: string;
  key_skills?: string[]; // JSON array
  experience_years?: number;
  education?: any[]; // JSON array
  
  // Processing metadata
  analysis_complete?: boolean;
  processing_status: ResumeStatus;
  processing_error?: string;
  ai_provider_used?: string;
  ai_model_used?: string;
  ai_processing_time?: number; // milliseconds
  processing_completed_at?: string;
  updated_at?: string;
  
  // Legacy/computed fields for backward compatibility
  name?: string;
  email?: string;
  aiScore?: number;
  date?: string;
  jobDescription?: string;
  resumeText?: string;
  questions?: string[];
  analysis_result?: any; // For backward compatibility
};

export type NavItem = {
  title: string;
  href: string;
  icon: React.ElementType;
  label?: string;
  disabled?: boolean;
};
