export interface SiliconFlowConfig {
  api_key: string
  base_url: string
  model: string
}

export interface ProfileDimension {
  value: string | string[]
  confidence: number
  updated_at: string
  evidence: string
}

export interface DynamicProfile {
  user_id: string
  version: number
  dimensions: Record<string, ProfileDimension>
  history: { role: string; content: string; created_at: string }[]
  updated_at: string | null
  completion: number
  dimension_catalog: string[]
}

export interface ProfileChatResponse {
  reply: string
  profile: DynamicProfile
  updated_dimensions: string[]
  provider: 'siliconflow' | 'rule-fallback'
  warning?: string
}

export interface ProfileInterviewResponse {
  question: string
  profile: DynamicProfile
  provider: 'siliconflow' | 'rule-fallback'
  warning?: string
}
