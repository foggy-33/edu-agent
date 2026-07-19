import type {
  LearningRequest,
  EvaluateRequest,
  GenerateResponse,
  EvaluateResponse,
  Course,
  StudentProfile,
  CollaborativeLearningRequest,
  CollaborativeLearningResponse,
  UploadedResource,
  CoursePdfMaterial,
  CoursePdfAnnotation
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
    throw new Error(data?.detail || `璇锋眰澶辫触: ${response.status} ${response.statusText}`)
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

export async function listCourseMaterials(course: string): Promise<{ materials: CoursePdfMaterial[] }> {
  return httpRequest(`${API_BASE}/course-materials?course=${encodeURIComponent(course)}`)
}

export function courseMaterialPreviewUrl(course: string, materialId: string): string {
  return `${API_BASE}/course-materials/${encodeURIComponent(materialId)}/preview?course=${encodeURIComponent(course)}`
}

export async function listCoursePdfAnnotations(
  userId: string,
  course: string,
  materialId: string
): Promise<{ annotations: CoursePdfAnnotation[] }> {
  const params = new URLSearchParams({ user_id: userId, course })
  return httpRequest(`${API_BASE}/course-materials/${encodeURIComponent(materialId)}/annotations?${params}`)
}

export async function addCoursePdfAnnotation(
  materialId: string,
  payload: {
    user_id: string
    course: string
    page: number
    content: string
    x: number | null
    y: number | null
  }
): Promise<{ annotation: CoursePdfAnnotation }> {
  return httpRequest(`${API_BASE}/course-materials/${encodeURIComponent(materialId)}/annotations`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function deleteCoursePdfAnnotation(
  materialId: string,
  annotationId: string,
  userId: string,
  course: string
): Promise<void> {
  const params = new URLSearchParams({ user_id: userId, course })
  return httpRequest(
    `${API_BASE}/course-materials/${encodeURIComponent(materialId)}/annotations/${encodeURIComponent(annotationId)}?${params}`,
    { method: 'DELETE' }
  )
}

export async function generateLearningResources(payload: CollaborativeLearningRequest): Promise<CollaborativeLearningResponse> {
  return httpRequest<CollaborativeLearningResponse>(`${API_BASE}/learning/generate`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function getWorkflow(): Promise<Record<string, unknown>> {
  return httpRequest<Record<string, unknown>>(`${API_BASE}/workflow`)
}

export async function testSiliconFlow(config: SiliconFlowConfig): Promise<{ status: string; model: string; message: string }> {
  return httpRequest(`${API_BASE}/settings/siliconflow/test`, {
    method: 'POST',
    body: JSON.stringify(config)
  })
}

export async function exportOfficeFile(payload: {
  title: string
  subtitle: string
  content: string
  format: 'pptx' | 'docx'
}): Promise<Blob> {
  const response = await fetch(`${API_BASE}/exports/office`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail || 'Office 文件生成失败')
  }
  return response.blob()
}

export async function testSpark(config: SiliconFlowConfig): Promise<{ status: string; model: string; message: string }> {
  return httpRequest(`${API_BASE}/settings/spark/test`, {
    method: 'POST',
    body: JSON.stringify(config)
  })
}

export async function testOpenAICompatible(config: SiliconFlowConfig): Promise<{ status: string; model: string; message: string }> {
  return httpRequest(`${API_BASE}/settings/openai/test`, {
    method: 'POST',
    body: JSON.stringify(config)
  })
}

export async function getDynamicProfile(userId: string, course?: string): Promise<{ profile: DynamicProfile }> {
  const params = course ? `?course=${encodeURIComponent(course)}` : ''
  return httpRequest(`${API_BASE}/profiles/${encodeURIComponent(userId)}${params}`)
}

export async function uploadResource(
  userId: string,
  file: File,
  courseFolder: string
): Promise<{ resource: UploadedResource }> {
  const body = new FormData()
  body.append('user_id', userId)
  body.append('course_folder', courseFolder)
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

export async function saveGeneratedResource(payload: {
  user_id: string
  name: string
  content: string
  resource_type: string
  course_folder: string
}): Promise<{ resource: UploadedResource }> {
  return httpRequest<{ resource: UploadedResource }>(`${API_BASE}/resources/generated`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateResourceFolder(
  userId: string,
  fileId: string,
  courseFolder: string
): Promise<{ resource: UploadedResource }> {
  return httpRequest<{ resource: UploadedResource }>(`${API_BASE}/resources/${encodeURIComponent(fileId)}/folder`, {
    method: 'PUT',
    body: JSON.stringify({ user_id: userId, course_folder: courseFolder }),
  })
}

export async function listCategories(userId: string): Promise<{ categories: Array<{ name: string; count: number }> }> {
  return httpRequest(`${API_BASE}/resources/categories/list?user_id=${encodeURIComponent(userId)}`)
}

export function resourceDownloadUrl(userId: string, fileId: string): string {
  return `${API_BASE}/resources/${encodeURIComponent(fileId)}/download?user_id=${encodeURIComponent(userId)}`
}

export function resourcePreviewUrl(userId: string, fileId: string): string {
  return `${API_BASE}/resources/${encodeURIComponent(fileId)}/preview?user_id=${encodeURIComponent(userId)}`
}

export async function getResourceContent(userId: string, fileId: string): Promise<{ content: string }> {
  return httpRequest(`${API_BASE}/resources/${encodeURIComponent(fileId)}/content?user_id=${encodeURIComponent(userId)}`)
}

export async function listDynamicProfiles(userId: string): Promise<{ profiles: SubjectProfileSummary[] }> {
  return httpRequest(`${API_BASE}/profiles/${encodeURIComponent(userId)}/subjects`)
}

export async function getLearningStats(userId: string, course?: string): Promise<{ stats: any }> {
  const params = course ? `?course=${encodeURIComponent(course)}` : ''
  return httpRequest(`${API_BASE}/learning/stats/${encodeURIComponent(userId)}${params}`)
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

export interface MistakeRecord {
  question_id: string
  question: string
  type: string
  chapter: string
  level: string
  options: { label: string; text: string }[] | null
  student_answer: string
  correct_answer: string
  analysis: string
  topic: string
  course_name?: string
  mistake_count: number
  review_count: number
  mastered: boolean
  last_mistake_at: string
}

export async function addMistake(payload: {
  user_id: string
  course: string
  question_id: string
  question: string
  type: string
  chapter: string
  level: string
  options: { label: string; text: string }[] | null
  answer: string
  correct_answer: string
  analysis: string
  topic: string
}): Promise<{ status: string }> {
  return httpRequest<{ status: string }>(`${API_BASE}/mistakes/add`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function listMistakes(userId: string, course: string): Promise<{ mistakes: MistakeRecord[] }> {
  return httpRequest<{ mistakes: MistakeRecord[] }>(`${API_BASE}/mistakes/list?user_id=${encodeURIComponent(userId)}&course=${encodeURIComponent(course)}`)
}

export async function listAllMistakes(userId: string, mastered: boolean = false): Promise<{ mistakes: MistakeRecord[] }> {
  return httpRequest<{ mistakes: MistakeRecord[] }>(`${API_BASE}/mistakes/all?user_id=${encodeURIComponent(userId)}&mastered=${mastered}`)
}

export async function getMistakeStats(userId: string): Promise<{ stats: { course_name: string; unmastered_count: number; mastered_count: number; total_count: number }[] }> {
  return httpRequest<{ stats: { course_name: string; unmastered_count: number; mastered_count: number; total_count: number }[] }>(`${API_BASE}/mistakes/stats?user_id=${encodeURIComponent(userId)}`)
}

export async function markMistakeMastered(userId: string, course: string, questionId: string): Promise<{ status: string }> {
  const body = new FormData()
  body.append('user_id', userId)
  body.append('course', course)
  body.append('question_id', questionId)
  return httpRequest<{ status: string }>(`${API_BASE}/mistakes/master`, {
    method: 'POST',
    body
  })
}

export async function markMistakeMasteredAny(userId: string, questionId: string): Promise<{ status: string }> {
  return httpRequest<{ status: string }>(`${API_BASE}/mistakes/master-any?user_id=${encodeURIComponent(userId)}&question_id=${encodeURIComponent(questionId)}`, {
    method: 'POST'
  })
}

export async function getWeakTopics(userId: string, course: string): Promise<{ topics: string[] }> {
  return httpRequest<{ topics: string[] }>(`${API_BASE}/mistakes/weak-topics?user_id=${encodeURIComponent(userId)}&course=${encodeURIComponent(course)}`)
}

export async function analyzeMistakeWeakTopics(payload: SiliconFlowConfig & {
  user_id: string
  course?: string
}): Promise<{ courses: Array<{ course: string; points: string[] }>; provider: string }> {
  return httpRequest(`${API_BASE}/mistakes/analyze-weak-topics`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
