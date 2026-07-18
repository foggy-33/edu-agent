export interface SiliconFlowConfig {
  active_provider: 'siliconflow' | 'spark'
  api_key: string
  base_url: string
  model: string
  spark_api_password: string
  spark_base_url: string
  spark_model: string
}

export interface ProfileDimension {
  value: string | string[]
  confidence: number
  updated_at: string
  evidence: string
}

export interface DynamicProfile {
  user_id: string
  course: string
  version: number
  dimensions: Record<string, ProfileDimension>
  history: { role: string; content: string; created_at: string }[]
  updated_at: string | null
  completion: number
  dimension_catalog: string[]
  radar_catalog: Record<string, string>
  radar_metrics: Record<string, number>
  radar_summaries: Record<string, string>
  llm_context: {
    schema_version: string
    instruction: string
    user_id: string
    course: string
    summary: string
    facts: Record<string, string | string[]>
    weak_points: string[]
    resource_preferences: string[]
    radar_metrics: Record<string, number>
    radar_summaries: Record<string, string>
    completion: number
    updated_at: string | null
  }
}

export interface SubjectProfileSummary {
  course: string
  version: number
  completion: number
  updated_at: string | null
  summary: string
  radar_metrics: Record<string, number>
}

export interface ProfileChatResponse {
  reply: string
  profile: DynamicProfile
  updated_dimensions: string[]
  provider: 'siliconflow' | 'spark' | 'rule-fallback'
  warning?: string
}

export interface ProfileInterviewResponse {
  question: string
  profile: DynamicProfile
  provider: 'siliconflow' | 'spark' | 'rule-fallback'
  warning?: string
}
