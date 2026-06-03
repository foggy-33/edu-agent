import type {
  LearningRequest,
  EvaluateRequest,
  GenerateResponse,
  EvaluateResponse,
  Course,
  StudentProfile
} from '../types'

const API_BASE = '/api'

async function httpRequest<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    }
  })

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status} ${response.statusText}`)
  }

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
