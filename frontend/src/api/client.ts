import type {
  LearningRequest,
  EvaluateRequest,
  GenerateResponse,
  EvaluateResponse,
  Course,
  StudentProfile
  , CollaborativeLearningRequest
  , CollaborativeLearningResponse
  , UploadedResource
} from '../types'
import type { DynamicProfile, ProfileChatResponse, ProfileInterviewResponse, SiliconFlowConfig, SubjectProfileSummary } from '../types/profile'

const API_BASE = '/api'

async function httpRequest<T>(url: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options?.headers || {})
    }
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail || `请求失败: ${response.status} ${response.statusText}`)
  }

  if (response.status === 204) return undefined as T
  return response.json()
}

export async function analyze(payload: LearningRequest): Promise<{ profile: StudentProfile }> {
  return httpRequest<{ profile: StudentProfile }>(`${API_BASE}/analyze`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function generate(payload: LearningRequest): Promise<GenerateResponse> {
  return httpRequest<GenerateResponse>(`${API_BASE}/generate`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function evaluate(payload: EvaluateRequest): Promise<EvaluateResponse> {
  return httpRequest<EvaluateResponse>(`${API_BASE}/evaluate`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function getCourses(): Promise<{ courses: Course[] }> {
  return httpRequest<{ courses: Course[] }>(`${API_BASE}/courses`)
}

export async function getWorkflow(): Promise<Record<string, unknown>> {
  return httpRequest<Record<string, unknown>>(`${API_BASE}/workflow`)
}

export async function generateCollaborativeLearning(payload: CollaborativeLearningRequest): Promise<CollaborativeLearningResponse> {
  return httpRequest<CollaborativeLearningResponse>(`${API_BASE}/learning/generate`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function testSiliconFlow(config: SiliconFlowConfig): Promise<{ status: string; model: string; message: string }> {
  return httpRequest(`${API_BASE}/settings/siliconflow/test`, {
    method: 'POST',
    body: JSON.stringify(config)
  })
}

export async function getDynamicProfile(userId: string, course?: string): Promise<{ profile: DynamicProfile }> {
  const params = course ? `?course=${encodeURIComponent(course)}` : ''
  return httpRequest(`${API_BASE}/profiles/${encodeURIComponent(userId)}${params}`)
}

export async function uploadResource(userId: string, file: File): Promise<{ resource: UploadedResource }> {
  const body = new FormData()
  body.append('user_id', userId)
  body.append('file', file)
  return httpRequest<{ resource: UploadedResource }>(`${API_BASE}/resources/upload`, {
    method: 'POST',
    body,
  })
}

export async function listResources(userId: string): Promise<{ resources: UploadedResource[] }> {
  return httpRequest<{ resources: UploadedResource[] }>(`${API_BASE}/resources?user_id=${encodeURIComponent(userId)}`)
}

export async function deleteResource(userId: string, fileId: string): Promise<void> {
  return httpRequest<void>(`${API_BASE}/resources/${encodeURIComponent(fileId)}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE',
  })
}

export function resourceDownloadUrl(userId: string, fileId: string): string {
  return `${API_BASE}/resources/${encodeURIComponent(fileId)}/download?user_id=${encodeURIComponent(userId)}`
}

export async function listDynamicProfiles(userId: string): Promise<{ profiles: SubjectProfileSummary[] }> {
  return httpRequest(`${API_BASE}/profiles/${encodeURIComponent(userId)}/subjects`)
}

export async function chatDynamicProfile(payload: SiliconFlowConfig & {
  user_id: string
  course: string
  message: string
}): Promise<ProfileChatResponse> {
  return httpRequest(`${API_BASE}/profiles/chat`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function getNextProfileQuestion(payload: SiliconFlowConfig & {
  user_id: string
  course: string
}): Promise<ProfileInterviewResponse> {
  return httpRequest(`${API_BASE}/profiles/interview/next`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function smartEvaluate(payload: { user_id: string; course: string }): Promise<any> {
  return httpRequest(`${API_BASE}/evaluate/smart`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function startQuiz(payload: { user_id: string; course: string }): Promise<any> {
  return httpRequest(`${API_BASE}/evaluate/quiz/start`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function answerQuiz(payload: { user_id: string; course: string; question_id: string; answer: string }): Promise<any> {
  return httpRequest(`${API_BASE}/evaluate/quiz/answer`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function finishQuiz(payload: { user_id: string; course: string }): Promise<any> {
  return httpRequest(`${API_BASE}/evaluate/quiz/finish`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export interface PracticeRecord {
  record_id: string
  date: string
  chapter: string
  question: string
  user_answer: string
  correct_answer: string
  is_correct: boolean
}

export async function getPracticeRecords(userId: string, course?: string): Promise<{ records: PracticeRecord[] }> {
  const params = course ? `?course=${encodeURIComponent(course)}` : ''
  return httpRequest<{ records: PracticeRecord[] }>(`${API_BASE}/practice/records/${encodeURIComponent(userId)}${params}`)
}
