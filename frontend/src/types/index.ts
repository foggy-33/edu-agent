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
  extended_reading: { title: string; source: string; reason: string }[]
}

export interface RetrievalMeta {
  query: string
  keyword_count: number
  vector_count: number
  mode: 'hybrid' | 'keyword'
  vector_error: string
}

export interface SafetyReport {
  status: 'pass' | 'warning'
  notes: string[]
}

export interface GenerateResponse {
  profile: StudentProfile
  learning_path: LearningPathItem[]
  resources: Resources
  retrieval_meta?: RetrievalMeta
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

export interface QuestionOption {
  label: string
  text: string
}

export interface Question {
  id: number | string
  type: 'single' | 'multiple' | 'judge' | 'fill' | 'short'
  chapter: string
  question: string
  options?: QuestionOption[]
  answer: string | string[] | boolean
  analysis: string
  level?: string
}

export interface CourseChapter {
  id: number | string
  name: string
  hours: number
  status: 'completed' | 'current' | 'pending' | string
  topics?: string[]
}

export interface Course {
  id: number | string
  name: string
  icon: string
  description?: string
  progress: number
  totalHours: number
  completedHours: number
  status: 'in-progress' | 'completed' | 'not-started' | string
  lastAccess: string
  difficulty: '简单' | '中等' | '困难' | string
  chapters?: CourseChapter[]
  goals?: string[]
  suggestions?: string[]
  questions: Question[]
}

export interface CoursePdfMaterial {
  id: string
  name: string
  filename: string
  size: number
}

export interface CoursePdfAnnotation {
  id: string
  page: number
  content: string
  x: number | null
  y: number | null
  created_at: string
}

export type CollaborativeResourceType = 'lecture' | 'mindmap' | 'exercise' | 'reading' | 'code' | 'path' | 'ppt' | 'word'

export interface CollaborativeLearningRequest {
  user_id: string
  major: string
  course: string
  chapter: string
  weakness: string
  goal: string
  resourceTypes: CollaborativeResourceType[]
  fileIds: string[]
  active_provider: 'siliconflow' | 'spark' | 'openai'
  api_key: string
  base_url: string
  model: string
  spark_api_password: string
  spark_base_url: string
  spark_model: string
  openai_model: string
  response_speed?: 'fast' | 'balanced' | 'deep'
}

export interface AgentTraceItem {
  order: number
  agent: string
  status: string
  summary: string
  timestamp: string
}

export interface CollaborativeExerciseOption {
  label: string
  text: string
}

export interface CollaborativeExerciseItem {
  id: string
  level: string
  type: 'single' | 'judge' | 'fill' | 'short'
  question: string
  options: CollaborativeExerciseOption[]
  answer: string
  explanation: string
}

export interface CollaborativeLearningResponse {
  lectureDoc: string
  mindmap: string
  exercises: string
  exerciseItems: CollaborativeExerciseItem[]
  reading: string
  codeCase: string
  learningPath: string
  presentation: string
  wordDocument: string
  review: string
  sources: Pick<UploadedResource, 'id' | 'name' | 'page_count'>[]
  agentTrace: AgentTraceItem[]
}

export interface UploadedResource {
  id: string
  user_id: string
  name: string
  type: 'pdf' | 'markdown' | 'mindmap' | 'lecture' | 'review' | 'reading' | 'exercises' | 'path'
  size: number
  page_count: number
  text_length: number
  status: 'ready'
  course_folder: string
  source_type: 'uploaded' | 'generated'
  created_at: string
  summary?: string
}
