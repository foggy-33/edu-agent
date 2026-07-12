<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { loadUserProfile } from '../api/userProfile'
import { listAllMistakes, listMistakes, markMistakeMastered, markMistakeMasteredAny } from '../api/client'
import type { Question } from '../types'
import type { MistakeRecord } from '../api/client'

const props = defineProps<{
  course: { id: string | number; name: string }
}>()

const emit = defineEmits<{
  navigate: [page: 'courses' | 'detail' | 'exercise' | 'mistakes']
}>()

const mistakes = ref<Question[]>([])
const loading = ref(false)
const currentIndex = ref(0)
const selectedAnswers = ref<Record<string, string>>({})
const showResult = ref(false)
const masteredCount = ref(0)
const showCompletion = ref(false)
const totalAnswered = ref(0)
const correctAnswered = ref(0)
const showCourseList = ref(true)
const allMistakes = ref<MistakeRecord[]>([])
const currentTab = ref<'unmastered' | 'mastered'>('unmastered')
const selectedCourseName = ref('')

const filterCourse = ref<string>('')
const filterMastered = ref<string>('all')
const filterMinCount = ref<number>(0)

type PracticeMode = 'sequential' | 'random'
type PracticeScope = 'unmastered' | 'mixed'

const practiceMode = ref<PracticeMode>('sequential')
const practiceScope = ref<PracticeScope>('unmastered')
const showPracticeSettings = ref(false)

interface AnswerRecord {
  question: Question
  userAnswer: string
  isCorrect: boolean
}

const answerRecords = ref<AnswerRecord[]>([])

const currentQuestion = computed(() => mistakes.value[currentIndex.value])

const progressText = computed(() => {
  return `${currentIndex.value + 1} / ${mistakes.value.length}`
})

function mistakeToQuestion(mistake: MistakeRecord & { course_name?: string }): Question {
  return {
    id: mistake.question_id,
    type: (mistake.type as Question['type']) || 'short',
    chapter: mistake.chapter,
    question: mistake.question,
    options: mistake.options || undefined,
    answer: mistake.correct_answer,
    analysis: mistake.analysis,
    level: mistake.level,
  }
}

const filteredMistakes = computed(() => {
  return allMistakes.value.filter(m => {
    if (filterCourse.value && m.course_name !== filterCourse.value) {
      return false
    }
    if (filterMastered.value === 'unmastered' && m.mastered) {
      return false
    }
    if (filterMastered.value === 'mastered' && !m.mastered) {
      return false
    }
    if (filterMinCount.value > 0 && (m.mistake_count || 1) < filterMinCount.value) {
      return false
    }
    return true
  })
})

const courses = computed(() => {
  const set = new Set<string>()
  allMistakes.value.forEach(m => {
    set.add(m.course_name || '')
  })
  return Array.from(set).filter(Boolean)
})

async function loadMistakesList() {
  loading.value = true
  try {
    const userProfile = loadUserProfile()
    const response = await listAllMistakes(userProfile.userId, false)
    allMistakes.value = response.mistakes || []
  } catch {
    allMistakes.value = []
  } finally {
    loading.value = false
  }
}

async function loadMistakes() {
  loading.value = true
  try {
    const userProfile = loadUserProfile()
    const isMastered = currentTab.value === 'mastered'
    const courseName = selectedCourseName.value || props.course.name
    
    if (courseName === '全部错题') {
      const response = await listAllMistakes(userProfile.userId, isMastered)
      mistakes.value = (response.mistakes || []).map(mistakeToQuestion)
    } else {
      const response = await listMistakes(userProfile.userId, courseName)
      mistakes.value = (response.mistakes || []).filter(m => m.mastered === isMastered).map(mistakeToQuestion)
    }
    currentIndex.value = 0
    showResult.value = false
  } catch {
    mistakes.value = []
  } finally {
    loading.value = false
  }
}

function startAllPractice() {
  showPracticeSettings.value = true
}

function confirmPractice() {
  let practiceMistakes = [...filteredMistakes.value]
  
  if (practiceScope.value === 'unmastered') {
    practiceMistakes = practiceMistakes.filter(m => !m.mastered)
  }
  
  if (practiceMode.value === 'random') {
    practiceMistakes = shuffleArray(practiceMistakes)
  }
  
  if (practiceMistakes.length === 0) {
    alert('没有符合条件的错题可练习')
    return
  }
  
  showPracticeSettings.value = false
  showCourseList.value = false
  showCompletion.value = false
  totalAnswered.value = 0
  correctAnswered.value = 0
  masteredCount.value = 0
  answerRecords.value = []
  selectedAnswers.value = {}
  mistakes.value = practiceMistakes.map(mistakeToQuestion)
  currentIndex.value = 0
  showResult.value = false
}

function cancelPractice() {
  showPracticeSettings.value = false
}

function shuffleArray<T>(array: T[]): T[] {
  const result = [...array]
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

function backToCourseList() {
  showCourseList.value = true
  selectedCourseName.value = ''
  mistakes.value = []
  loadMistakesList()
}

function selectAnswer(answer: string) {
  if (!currentQuestion.value || showResult.value) return
  const q = currentQuestion.value as any
  const qid = q.question_id !== undefined ? String(q.question_id) : String(q.id)
  if (currentQuestion.value.type === 'multiple') {
    const current = selectedAnswers.value[qid]?.split('').filter(Boolean) || []
    const next = current.includes(answer)
      ? current.filter(item => item !== answer)
      : [...current, answer].sort()
    selectedAnswers.value = { ...selectedAnswers.value, [qid]: next.join('') }
  } else {
    selectedAnswers.value = { ...selectedAnswers.value, [qid]: answer }
  }
}

function normalizeAnswer(value: unknown) {
  return String(value ?? '').trim().replace(/\s+/g, '').toLowerCase()
}

function checkAnswer(): boolean {
  if (!currentQuestion.value) return false
  const q = currentQuestion.value as any
  const qid = q.question_id !== undefined ? String(q.question_id) : String(q.id)
  const selected = selectedAnswers.value[qid] || ''
  // 优先使用 correct_answer（正确答案），而不是 answer（用户之前的错误答案）
  const correctAnswer = q.correct_answer !== undefined && q.correct_answer !== '' 
    ? q.correct_answer 
    : q.answer
  
  if (typeof correctAnswer === 'boolean') {
    return normalizeAnswer(selected) === normalizeAnswer(correctAnswer ? '正确' : '错误')
      || normalizeAnswer(selected) === normalizeAnswer(String(correctAnswer))
  }
  if (Array.isArray(correctAnswer)) {
    return normalizeAnswer(selected) === normalizeAnswer(correctAnswer.join(''))
  }
  return normalizeAnswer(selected) === normalizeAnswer(correctAnswer)
}

async function submitAnswer() {
  if (!currentQuestion.value || showResult.value) return
  showResult.value = true
  totalAnswered.value++

  const q = currentQuestion.value as any
  const qid = q.question_id !== undefined ? String(q.question_id) : String(q.id)
  const userAnswer = selectedAnswers.value[qid] || ''
  const isCorrect = checkAnswer()

  answerRecords.value.push({
    question: currentQuestion.value,
    userAnswer: userAnswer,
    isCorrect: isCorrect
  })

  if (isCorrect) {
    correctAnswered.value++
    masteredCount.value++
    const userProfile = loadUserProfile()
    const questionId = q.question_id !== undefined ? String(q.question_id) : String(q.id)
    if (props.course.name === '全部错题') {
      await markMistakeMasteredAny(userProfile.userId, questionId)
    } else {
      await markMistakeMastered(userProfile.userId, props.course.name, questionId)
    }
    (currentQuestion.value as any).justMastered = true
  }
}

function nextQuestion() {
  if ((currentQuestion.value as any)?.justMastered) {
    mistakes.value.splice(currentIndex.value, 1)
    if (mistakes.value.length === 0) {
      showCompletion.value = true
      return
    }
    if (currentIndex.value >= mistakes.value.length) {
      currentIndex.value = mistakes.value.length - 1
    }
    showResult.value = false
  } else if (currentIndex.value < mistakes.value.length - 1) {
    currentIndex.value++
    showResult.value = false
  } else {
    showCompletion.value = true
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    showResult.value = false
  }
}

function resetAndContinue() {
  showCompletion.value = false
  totalAnswered.value = 0
  correctAnswered.value = 0
  masteredCount.value = 0
  answerRecords.value = []
  selectedAnswers.value = {}
  mistakes.value = []
  showCourseList.value = true
  loadMistakesList()
}

function getQuestionTypeLabel(type: string | undefined): string {
  const types: Record<string, string> = {
    'choice': '选择题',
    'single': '单选题',
    'multiple': '多选题',
    'judge': '判断题',
    'fill': '填空题',
    'short': '简答题',
    'essay': '论述题'
  }
  return types[type || ''] || (type || '其他')
}

function judgeOptions(question: Question) {
  if (question.options?.length) return question.options
  return [{ label: '正确', text: '正确' }, { label: '错误', text: '错误' }]
}

function optionsFor(question: Question) {
  return question.type === 'judge' ? judgeOptions(question) : (question.options || [])
}

function getOptionClass(optionLabel: string) {
  if (!currentQuestion.value) return ''
  const q = currentQuestion.value as any
  const qid = q.question_id !== undefined ? String(q.question_id) : String(q.id)
  const selectedValue = selectedAnswers.value[qid] || ''
  const selected = currentQuestion.value.type === 'multiple'
    ? selectedValue.includes(optionLabel)
    : selectedValue === optionLabel
  if (!showResult.value) return selected ? 'option-selected' : ''

  // 优先使用 correct_answer（正确答案）
  const correctAnswer = q.correct_answer !== undefined && q.correct_answer !== '' 
    ? q.correct_answer 
    : q.answer
  const correct = Array.isArray(correctAnswer)
    ? correctAnswer.map(String).includes(optionLabel)
    : normalizeAnswer(optionLabel) === normalizeAnswer(correctAnswer)
  if (correct) return 'option-correct'
  if (selected && !correct) return 'option-wrong'
  return 'option-muted'
}

onMounted(() => {
  if (props.course.name === '全部错题') {
    loadMistakesList()
  } else {
    loadMistakes()
  }
})
</script>

<template>
  <div class="mistake-book-page">
    <section class="quiz-shell">
      <header class="quiz-header">
        <div>
          <h1>{{ showCourseList ? '错题本' : (selectedCourseName || course.name) + ' - 错题练习' }}</h1>
          <p>{{ showCourseList ? '选择课程开始错题练习' : (currentTab === 'unmastered' ? '待复习' : '已掌握') + '：' + mistakes.length + ' 题' }}</p>
        </div>
        <div class="quiz-header-actions">
          <button v-if="!showCourseList" type="button" title="返回课程列表" @click="backToCourseList">↺</button>
          <button type="button" title="返回" @click="showCourseList || course.name === '全部错题' ? emit('navigate', 'courses') : emit('navigate', 'detail')">↩</button>
          <button type="button" title="退出" @click="emit('navigate', 'courses')">×</button>
        </div>
      </header>

      <template v-if="showCourseList">
        <div v-if="loading" class="quiz-loading">
          <div></div>
          <strong>加载错题列表中...</strong>
        </div>

        <div v-else-if="allMistakes.length === 0" class="empty-state">
          <div>🎉</div>
          <h2>太棒了！没有错题</h2>
          <p>继续保持，定期练习巩固知识</p>
          <button class="primary-button" @click="emit('navigate', 'courses')">去学习</button>
        </div>

        <div v-else>
          <div class="mistake-filters">
            <div class="filter-group">
              <label>课程：</label>
              <select v-model="filterCourse" class="filter-select">
                <option value="">全部课程</option>
                <option v-for="course in courses" :key="course" :value="course">{{ course }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>掌握情况：</label>
              <select v-model="filterMastered" class="filter-select">
                <option value="all">全部</option>
                <option value="unmastered">待复习</option>
                <option value="mastered">已掌握</option>
              </select>
            </div>
            <div class="filter-group">
              <label>错误次数 ≥：</label>
              <select v-model="filterMinCount" class="filter-select">
                <option :value="0">不限</option>
                <option :value="2">2次</option>
                <option :value="3">3次</option>
                <option :value="5">5次</option>
              </select>
            </div>
          </div>

          <div class="mistake-list-header">
            <span>共 {{ filteredMistakes.length }} 道错题</span>
            <button class="primary-button" @click="startAllPractice">开始错题练习</button>
          </div>

          <div class="mistake-list">
            <div 
              v-for="(mistake, index) in filteredMistakes" 
              :key="index"
              class="mistake-list-item"
            >
              <div class="mistake-item-index">{{ index + 1 }}</div>
              <div class="mistake-item-content">
                <div class="mistake-item-header">
                  <span class="mistake-item-course">{{ mistake.course_name }}</span>
                  <span class="mistake-item-type">{{ getQuestionTypeLabel(mistake.type) }}</span>
                  <span class="mistake-item-count">错{{ mistake.mistake_count || 1 }}次</span>
                </div>
                <p class="mistake-item-question">{{ mistake.question }}</p>
                <div class="mistake-item-footer">
                  <span class="mistake-item-chapter">{{ mistake.chapter || '综合' }}</span>
                  <span :class="['mistake-item-status', mistake.mastered ? 'mastered' : 'unmastered']">
                    {{ mistake.mastered ? '已掌握' : '待复习' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="quiz-progress">
          <div class="progress-segments">
            <span
              v-for="(_, index) in mistakes"
              :key="index"
              :class="{ active: index <= currentIndex, answered: index < currentIndex || (index === currentIndex && showResult) }"
            ></span>
          </div>
          <b>{{ progressText }}</b>
        </div>

        <div v-if="loading" class="quiz-loading">
          <div></div>
          <strong>加载错题中...</strong>
        </div>

      <div v-else-if="showCompletion" class="completion-state">
        <h2>练习完成！</h2>
        <div class="completion-score">
          <div class="score-circle">
            <span class="score-value">{{ totalAnswered > 0 ? Math.round((correctAnswered / totalAnswered) * 100) : 0 }}</span>
            <span class="score-unit">分</span>
          </div>
          <div class="score-details">
            <p>答对 {{ correctAnswered }} 题</p>
            <p>答错 {{ totalAnswered - correctAnswered }} 题</p>
            <p>掌握 {{ masteredCount }} 题</p>
          </div>
        </div>
        <p class="completion-feedback">
          {{ correctAnswered === totalAnswered 
            ? '太棒了！所有错题都已掌握，继续保持！' 
            : (correctAnswered >= totalAnswered * 0.8 
              ? '表现优秀！大部分错题已经掌握，再接再厉！' 
              : (correctAnswered >= totalAnswered * 0.6 
                ? '表现不错，还有一些错题需要复习。' 
                : '还需要多加练习，建议回顾相关知识点。')) }}
        </p>
        
        <div class="answer-details">
          <h3>答题详情</h3>
          <div class="answer-list">
            <div 
              v-for="(record, index) in answerRecords" 
              :key="index"
              class="answer-item"
              :class="{ correct: record.isCorrect, wrong: !record.isCorrect }"
            >
              <div class="answer-item-header">
                <span class="answer-number">第 {{ index + 1 }} 题</span>
                <span :class="['answer-status', record.isCorrect ? 'correct' : 'wrong']">
                  {{ record.isCorrect ? '✓ 正确' : '✗ 错误' }}
                </span>
              </div>
              <div class="answer-item-content">
                <p class="question-text">{{ record.question.question }}</p>
                <div class="answer-compare">
                  <div class="answer-row">
                    <span class="label">你的答案：</span>
                    <span class="value">{{ record.userAnswer || '未作答' }}</span>
                  </div>
                  <div class="answer-row">
                    <span class="label">正确答案：</span>
                    <span class="value correct">{{ (record.question as any).correct_answer !== undefined && (record.question as any).correct_answer !== '' ? (record.question as any).correct_answer : record.question.answer }}</span>
                  </div>
                </div>
                <div v-if="record.question.analysis && !record.isCorrect" class="answer-analysis">
                  <span class="label">解析：</span>
                  <span class="value">{{ record.question.analysis }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="completion-actions">
          <button class="primary-button" @click="resetAndContinue">继续练习</button>
          <button class="ghost-button" @click="course.name === '全部错题' ? emit('navigate', 'courses') : emit('navigate', 'detail')">返回详情</button>
        </div>
      </div>

      <div v-else-if="mistakes.length === 0" class="empty-state">
        <div>🎉</div>
        <h2>太棒了！没有错题</h2>
        <p>继续保持，定期练习巩固知识</p>
        <button class="primary-button" @click="emit('navigate', 'exercise')">去练习</button>
      </div>

      <article v-else-if="currentQuestion" class="quiz-card">
        <div class="question-meta">
          <span>{{ currentQuestion.chapter }}</span>
          <span>{{ getQuestionTypeLabel(currentQuestion.type) }}</span>
          <span class="mistake-count">错 {{ (currentQuestion as any).mistake_count || 1 }} 次</span>
        </div>

        <div class="question-stack">
          <h2>第 {{ currentIndex + 1 }} 题</h2>
          <p>{{ currentQuestion.question }}</p>

          <div v-if="currentQuestion.type === 'single' || currentQuestion.type === 'multiple' || currentQuestion.type === 'judge'" class="stacked-options">
            <button
              v-for="option in optionsFor(currentQuestion)"
              :key="option.label"
              type="button"
              :disabled="showResult"
              :class="['exercise-option', getOptionClass(option.label)]"
              @click="selectAnswer(option.label)"
            >
              <b>{{ option.label }}.</b>
              <span>{{ option.text }}</span>
            </button>
          </div>

          <textarea
            v-else-if="currentQuestion.type === 'short'"
            :value="selectedAnswers[(currentQuestion as any).question_id !== undefined ? String((currentQuestion as any).question_id) : String(currentQuestion.id)]"
            :disabled="showResult"
            rows="5"
            class="answer-input"
            placeholder="请输入你的答案"
            @input="(e) => selectAnswer((e.target as HTMLTextAreaElement).value)"
          ></textarea>

          <input
            v-else
            :value="selectedAnswers[(currentQuestion as any).question_id !== undefined ? String((currentQuestion as any).question_id) : String(currentQuestion.id)]"
            :disabled="showResult"
            class="answer-input"
            placeholder="请输入答案"
            @input="(e) => selectAnswer((e.target as HTMLInputElement).value)"
          />
        </div>

        <div v-if="showResult" :class="['result-panel', checkAnswer() ? 'result-correct' : 'result-wrong']">
          <strong>{{ checkAnswer() ? '回答正确！已标记为掌握' : '回答错误' }}</strong>
          <p>参考答案：{{ (currentQuestion as any).correct_answer !== undefined && (currentQuestion as any).correct_answer !== '' ? (currentQuestion as any).correct_answer : currentQuestion.answer }}</p>
          <p>{{ currentQuestion.analysis }}</p>
        </div>

        <footer class="quiz-footer">
          <button type="button" class="ghost-button" :disabled="currentIndex === 0" @click="prevQuestion">
            上一个
          </button>
          <button
            v-if="!showResult"
            type="button"
            class="primary-button"
            :disabled="!((currentQuestion as any).question_id !== undefined ? selectedAnswers[String((currentQuestion as any).question_id)] : selectedAnswers[String(currentQuestion.id)])?.trim()"
            @click="submitAnswer"
          >
            提交
          </button>
          <button
            v-else-if="currentIndex < mistakes.length - 1"
            type="button"
            class="primary-button"
            @click="nextQuestion"
          >
            下一个
          </button>
          <button v-else type="button" class="primary-button" @click="showCompletion = true">
            完成
          </button>
        </footer>
      </article>
      </template>

      <Teleport to="body">
        <div v-if="showPracticeSettings" class="practice-settings-modal-overlay" @click="cancelPractice">
          <div class="practice-settings-modal" @click.stop>
            <h3>练习设置</h3>
            
            <div class="practice-setting-group">
              <label>练习模式：</label>
              <div class="practice-options">
                <button 
                  type="button" 
                  :class="['practice-option', practiceMode === 'sequential' ? 'active' : '']"
                  @click="practiceMode = 'sequential'"
                >顺序练习</button>
                <button 
                  type="button" 
                  :class="['practice-option', practiceMode === 'random' ? 'active' : '']"
                  @click="practiceMode = 'random'"
                >随机练习</button>
              </div>
            </div>
            
            <div class="practice-setting-group">
              <label>练习范围：</label>
              <div class="practice-options">
                <button 
                  type="button" 
                  :class="['practice-option', practiceScope === 'unmastered' ? 'active' : '']"
                  @click="practiceScope = 'unmastered'"
                >仅未掌握</button>
                <button 
                  type="button" 
                  :class="['practice-option', practiceScope === 'mixed' ? 'active' : '']"
                  @click="practiceScope = 'mixed'"
                >混合练习</button>
              </div>
            </div>
            
            <div class="practice-setting-summary">
              <span>共 {{ filteredMistakes.length }} 道错题</span>
            </div>
            
            <div class="practice-settings-actions">
              <button class="ghost-button" @click="cancelPractice">取消</button>
              <button class="primary-button" @click="confirmPractice">确认开始</button>
            </div>
          </div>
        </div>
      </Teleport>
    </section>
  </div>
</template>

<style scoped>
.mistake-book-page {
  min-height: calc(100vh - 72px);
  padding: 10px;
  background: #fff;
  color: #202123;
}

.quiz-shell {
  width: min(1180px, 100%);
  min-height: calc(100vh - 96px);
  margin: 0 auto;
  display: grid;
  grid-template-rows: auto auto 1fr;
  gap: 28px;
  padding: 30px 34px;
  border: 1px solid #e5e7eb;
  border-radius: 30px;
  background: #fff;
  box-shadow: 0 18px 48px rgba(15, 23, 42, .06);
}

.quiz-header,
.quiz-progress,
.quiz-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.quiz-header h1 {
  margin: 0;
  color: #1f2937;
  font-size: 18px;
  font-weight: 750;
}

.quiz-header p {
  margin: 7px 0 0;
  color: #8b8f98;
  font-size: 12px;
}

.quiz-header-actions {
  display: flex;
  gap: 10px;
}

.quiz-header-actions button {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 999px;
  color: #6b7280;
  background: #f3f4f6;
  font-size: 20px;
  line-height: 1;
}

.progress-segments {
  flex: 1;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(18px, 1fr);
  gap: 4px;
}

.progress-segments span {
  height: 6px;
  border-radius: 999px;
  background: #eceff3;
  transition: background .2s ease, transform .2s ease;
}

.progress-segments span.active {
  background: #d1d5db;
}

.progress-segments span.answered {
  background: #4b5563;
}

.quiz-progress b {
  min-width: 58px;
  color: #4b5563;
  text-align: right;
  font-size: 17px;
  font-weight: 700;
}

.quiz-loading {
  align-self: center;
  justify-self: center;
  display: grid;
  justify-items: center;
  gap: 12px;
  color: #4b5563;
  text-align: center;
}

.quiz-loading div {
  width: 38px;
  height: 38px;
  border: 2px solid #e5e7eb;
  border-top-color: #111827;
  border-radius: 50%;
  animation: spin .8s linear infinite;
}

.quiz-loading strong {
  color: #111827;
}

.empty-state {
  align-self: center;
  justify-self: center;
  text-align: center;
  padding: 60px 20px;
}

.empty-state div {
  font-size: 80px;
  margin-bottom: 20px;
}

.empty-state h2 {
  margin: 0 0 10px;
  font-size: 24px;
  color: #111827;
}

.empty-state p {
  margin: 0 0 24px;
  color: #8b8f98;
}

.quiz-card {
  width: min(760px, 100%);
  justify-self: center;
  display: grid;
  align-content: start;
  gap: 22px;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.question-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  color: #4b5563;
  background: #f3f4f6;
  font-size: 12px;
  font-weight: 650;
}

.question-meta .mistake-count {
  background: #fef2f2;
  color: #ef4444;
}

.question-meta .course-tag {
  background: #dbeafe;
  color: #1d4ed8;
}

.mistake-tabs {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 8px;
  background: #f9fafb;
  border-radius: 12px;
}

.tab-button {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-button:not(.tab-active) {
  background: #fff;
  color: #6b7280;
}

.tab-button:not(.tab-active):hover {
  background: #f3f4f6;
}

.tab-button.tab-active.unmastered {
  background: #ef4444;
  color: #fff;
}

.tab-button.tab-active.mastered {
  background: #10b981;
  color: #fff;
}

.question-stack {
  display: grid;
  gap: 18px;
}

.question-stack h2 {
  margin: 0;
  color: #111827;
  font-size: 18px;
  font-weight: 760;
}

.question-stack > p {
  margin: 0 0 8px;
  color: #1f2937;
  font-size: 18px;
  font-weight: 650;
  line-height: 1.75;
}

.stacked-options {
  display: grid;
  gap: 10px;
}

.mistake-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
  border: 1px solid #f3f4f6;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  min-width: 120px;
}

.filter-select:focus {
  outline: none;
  border-color: #3746b3;
  box-shadow: 0 0 0 2px rgba(55, 70, 179, 0.1);
}

.practice-settings {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  margin-bottom: 16px;
}

.practice-setting-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.practice-setting-group label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.practice-options {
  display: flex;
  gap: 8px;
}

.practice-option {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #6b7280;
  background: #fff;
  cursor: pointer;
  transition: all .2s ease;
}

.practice-option:hover {
  border-color: #3746b3;
  color: #3746b3;
}

.practice-option.active {
  background: #3746b3;
  color: #fff;
  border-color: #3746b3;
}

.practice-settings-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.practice-settings-modal {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}

.practice-settings-modal h3 {
  margin: 0 0 24px;
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
}

.practice-setting-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.practice-setting-group label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.practice-setting-summary {
  text-align: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  margin-bottom: 20px;
}

.practice-setting-summary span {
  font-size: 14px;
  color: #6b7280;
}

.practice-settings-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.mistake-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 0 4px;
}

.mistake-list-header span {
  font-size: 14px;
  color: #6b7280;
}

.mistake-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mistake-list-item {
  display: flex;
  gap: 16px;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
  border: 1px solid #f3f4f6;
}

.mistake-item-index {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3746b3;
  color: #fff;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

.mistake-item-content {
  flex: 1;
  min-width: 0;
}

.mistake-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.mistake-item-course {
  font-size: 12px;
  font-weight: 600;
  color: #3746b3;
  background: #eef2ff;
  padding: 3px 8px;
  border-radius: 6px;
}

.mistake-item-type {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 3px 8px;
  border-radius: 6px;
}

.mistake-item-count {
  font-size: 12px;
  color: #ef4444;
  background: #fef2f2;
  padding: 3px 8px;
  border-radius: 6px;
}

.mistake-item-question {
  margin: 0 0 8px;
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.mistake-item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mistake-item-chapter {
  font-size: 12px;
  color: #9ca3af;
}

.mistake-item-status {
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 999px;
}

.mistake-item-status.mastered {
  background: #d1fae5;
  color: #065f46;
}

.mistake-item-status.unmastered {
  background: #fef3c7;
  color: #92400e;
}

.exercise-option {
  width: 100%;
  min-height: 64px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  color: #1f2937;
  background: #f8fafc;
  text-align: left;
  font-size: 17px;
  font-weight: 620;
  transition: border-color .2s ease, background .2s ease, transform .2s ease;
}

.exercise-option:hover:not(:disabled),
.option-selected {
  border-color: #111827;
  background: #fff;
  transform: translateY(-1px);
}

.exercise-option b {
  min-width: 28px;
  color: #374151;
  font-size: 18px;
}

.exercise-option span {
  min-width: 0;
}

.option-correct {
  border-color: #22c55e;
  background: #f0fdf4;
  color: #166534;
}

.option-wrong {
  border-color: #ef4444;
  background: #fef2f2;
  color: #991b1b;
}

.option-muted {
  opacity: .56;
}

.answer-input {
  width: 100%;
  padding: 16px 18px;
  border: 1px solid #d1d5db;
  border-radius: 18px;
  outline: 0;
  resize: vertical;
  color: #111827;
  background: #fff;
  line-height: 1.7;
}

.answer-input:focus {
  border-color: #111827;
}

.result-panel {
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid;
}

.result-panel p {
  margin: 0;
  line-height: 1.7;
}

.result-correct {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.result-wrong {
  border-color: #fecaca;
  background: #fef2f2;
  color: #991b1b;
}

.quiz-footer {
  margin-top: auto;
  padding-top: 10px;
}

.ghost-button,
.primary-button {
  min-width: 92px;
  padding: 12px 20px;
  border: 0;
  border-radius: 999px;
  font-weight: 750;
}

.ghost-button {
  color: #4b5563;
  background: #f3f4f6;
}

.primary-button {
  color: #fff;
  background: #3746b3;
}

.ghost-button:disabled,
.primary-button:disabled {
  cursor: default;
  opacity: .45;
}

button {
  cursor: pointer;
}

.completion-state {
  align-self: center;
  justify-self: center;
  text-align: center;
  padding: 60px 20px;
}

.completion-state > div:first-child {
  font-size: 80px;
  margin-bottom: 20px;
}

.completion-state h2 {
  margin: 0 0 24px;
  font-size: 24px;
  color: #111827;
}

.completion-score {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  margin-bottom: 20px;
}

.score-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3746b3, #5c6bc0);
  color: #fff;
}

.score-value {
  font-size: 40px;
  font-weight: 800;
  line-height: 1;
}

.score-unit {
  font-size: 14px;
  margin-top: 4px;
}

.score-details {
  text-align: left;
}

.score-details p {
  margin: 8px 0;
  color: #4b5563;
  font-size: 14px;
}

.completion-feedback {
  max-width: 400px;
  margin: 0 auto 24px;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.6;
}

.completion-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.answer-details {
  width: 100%;
  max-width: 760px;
  margin-top: 24px;
}

.answer-details h3 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.answer-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.answer-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}

.answer-item.correct {
  border-left: 4px solid #10b981;
}

.answer-item.wrong {
  border-left: 4px solid #ef4444;
}

.answer-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.answer-number {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
}

.answer-status {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
}

.answer-status.correct {
  background: #d1fae5;
  color: #065f46;
}

.answer-status.wrong {
  background: #fee2e2;
  color: #991b1b;
}

.question-text {
  margin: 0 0 12px;
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
}

.answer-compare {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.answer-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.answer-row .label {
  color: #6b7280;
  font-weight: 500;
}

.answer-row .value {
  color: #374151;
}

.answer-row .value.correct {
  color: #10b981;
  font-weight: 600;
}

.answer-analysis {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e5e7eb;
  font-size: 14px;
  color: #6b7280;
}

.answer-analysis .label {
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 760px) {
  .mistake-book-page { padding: 0; }
  .quiz-shell { min-height: calc(100vh - 64px); padding: 22px 16px; border-radius: 0; border-left: 0; border-right: 0; }
  .quiz-header, .quiz-footer { align-items: flex-start; }
  .quiz-card { width: 100%; }
  .question-stack > p { font-size: 16px; }
  .exercise-option { min-height: 58px; padding: 15px 16px; font-size: 15px; }
}
</style>
