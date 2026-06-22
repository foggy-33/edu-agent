export interface LearningRequest {
  user_id: string
  course: string
  message: string
}

export interface AnswerRecord {
  question_id?: string
  question: string
  student_answer: string
  correct_answer?: string
  is_correct?: boolean
  topic?: string
}

export interface EvaluateRequest {
  user_id: string
  course: string
  answers: AnswerRecord[]
  message?: string
}

export interface StudentProfile {
  major: string
  course: string
  grade_level: string
  learning_goal: string
  knowledge_level: string
  weak_points: string[]
  learning_style: string
  resource_preference: string[]
}

export interface LearningPathItem {
  stage: number
  title: string
  goal: string
  tasks: string[]
  estimated_time: string
  recommended_resources: string[]
}

export interface QuizItem {
  question: string
  type: '选择题' | '判断题' | '填空题' | '简答题' | '应用题'
  answer: string
  explanation: string
}

export interface Resources {
  document: string
  mindmap: string
  quiz: QuizItem[]
  practice_case: string
  extended_reading: { title: string; url: string }[]
}

export interface SafetyReport {
  status: 'pass' | 'warning'
  notes: string[]
}

export interface GenerateResponse {
  profile: StudentProfile
  learning_path: LearningPathItem[]
  resources: Resources
  safety_report: SafetyReport
}

export interface EvaluateResponse {
  user_id: string
  course: string
  score_summary: Record<string, unknown>
  weak_points: string[]
  analysis: string
  next_steps: string[]
}

export interface Question {
  id: number
  type: 'single' | 'multiple' | 'judge'
  chapter: string
  question: string
  options?: { label: string; text: string }[]
  answer: string | string[] | boolean
  analysis: string
}

export interface Course {
  id: number
  name: string
  icon: string
  progress: number
  totalHours: number
  completedHours: number
  status: 'in-progress' | 'completed' | 'not-started' | string
  lastAccess: string
  difficulty: '简单' | '中等' | '困难' | string
  questions: Question[]
}
