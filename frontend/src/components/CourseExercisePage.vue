<script setup lang="ts">
import { computed, ref } from 'vue'
import { generateLearningResources, listResources, addMistake, getWeakTopics } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { CollaborativeExerciseItem, Course, Question, UploadedResource } from '../types'

const props = defineProps<{
  course: Course
  initialChapterId?: string | null
}>()

const emit = defineEmits<{
  navigate: [page: 'courses' | 'detail']
}>()

const loading = ref(false)
const generationError = ref('')
const currentQuestionIndex = ref(0)
const questions = ref<Question[]>([])
const selectedAnswers = ref<Record<string, string>>({})
const showResult = ref(false)
const answeredCount = ref(0)
const correctCount = ref(0)
const resources = ref<UploadedResource[]>([])
const showCompletion = ref(false)
const selectedChapterIds = ref<string[]>(props.initialChapterId ? [String(props.initialChapterId)] : [])
const questionTypes = ref<string[]>([])
const quizStarted = ref(false)

const allQuestionTypes = [
  { value: 'single', label: '单选题' },
  { value: 'multiple', label: '多选题' },
  { value: 'judge', label: '判断题' },
  { value: 'fill', label: '填空题' },
  { value: 'short', label: '简答题' },
]

interface AnswerRecord {
  question: Question
  userAnswer: string
  isCorrect: boolean
}
const answerRecords = ref<AnswerRecord[]>([])

const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])
const currentQuestionId = computed(() => String(currentQuestion.value?.id || ''))

const accuracy = computed(() => {
  return answeredCount.value > 0
    ? Math.round((correctCount.value / answeredCount.value) * 100)
    : 0
})

const currentAnswer = computed(() => selectedAnswers.value[currentQuestionId.value] || '')

function currentChapterNames() {
  if (selectedChapterIds.value.length > 0) {
    const selectedChapters = props.course.chapters?.filter(chapter => 
      selectedChapterIds.value.includes(String(chapter.id))
    )
    return selectedChapters?.map(chapter => chapter.name).join('、') || props.course.name
  }
  const active = props.course.chapters?.filter(chapter => chapter.status === 'current')
  const source = active?.length ? active : props.course.chapters
  return source?.map(chapter => chapter.name).join('、') || props.course.name
}

function normalizeAnswer(value: unknown) {
  return String(value ?? '').trim().replace(/\s+/g, '').toLowerCase()
}

function toQuestion(item: CollaborativeExerciseItem, index: number): Question {
  return {
    id: item.id || `ai-${index}`,
    type: item.type,
    chapter: item.level || currentChapterNames(),
    question: item.question,
    options: item.options || [],
    answer: item.answer,
    analysis: item.explanation,
    level: item.level,
  }
}

function fallbackQuestions(): Question[] {
  if (props.course.questions.length) {
    return props.course.questions
  }
  return [
    {
      id: `${props.course.id}-fallback`,
      type: 'short' as const,
      chapter: props.course.name,
      question: `请概括《${props.course.name}》当前阶段最重要的三个知识点，并说明它们之间的关系。`,
      options: [],
      answer: '围绕核心概念、适用条件和典型应用进行说明。',
      analysis: '开放题重点检查是否覆盖核心概念、适用条件、典型应用，以及知识点之间的联系。',
    },
  ]
}

async function loadResources() {
  try {
    const userProfile = loadUserProfile()
    const result = await listResources(userProfile.userId)
    resources.value = result.resources || []
  } catch (err) {
    console.error('加载资源失败', err)
    resources.value = []
  }
}

async function generateAiQuestions() {
  loading.value = true
  generationError.value = ''
  questions.value = []
  quizStarted.value = false
  try {
    const config = loadSiliconFlowConfig()
    const userProfile = loadUserProfile()

    await loadResources()

    const courseResources = resources.value.filter(
      r => r.course_folder === props.course.name || r.course_folder.includes(props.course.name)
    )
    const fileIds = courseResources.map(r => r.id)

    let weakness = props.course.suggestions?.join('；') || props.course.description || props.course.name
    try {
      const weakResponse = await getWeakTopics(userProfile.userId, props.course.name)
      if (weakResponse.topics?.length) {
        weakness = weakResponse.topics.join('；')
      }
    } catch (err) {
      console.log('获取薄弱点失败，使用默认值', err)
    }

    const typeLabels = questionTypes.value.length 
      ? questionTypes.value.map(t => allQuestionTypes.find(qt => qt.value === t)?.label || t).join('、')
      : '各种题型'
    
    const result = await generateLearningResources({
      user_id: userProfile.userId,
      major: userProfile.major || '计算机类',
      course: props.course.name,
      chapter: currentChapterNames(),
      weakness: weakness,
      goal: `针对《${props.course.name}》生成可直接作答的分层练习题，题型为：${typeLabels}，重点围绕薄弱点：${weakness}`,
      resourceTypes: ['exercise'],
      fileIds: fileIds,
      ...config,
    })
    questions.value = result.exerciseItems?.length
      ? result.exerciseItems.map(toQuestion)
      : fallbackQuestions()
    
    quizStarted.value = true
  } catch (reason) {
    generationError.value = reason instanceof Error ? reason.message : 'AI 生成练习题失败，已使用课程基础题'
    questions.value = fallbackQuestions()
    quizStarted.value = true
  } finally {
    loading.value = false
  }
}

function selectAnswer(answer: string) {
  if (showResult.value || !currentQuestion.value) return
  if (currentQuestion.value.type === 'multiple') {
    const current = selectedAnswers.value[currentQuestionId.value]?.split('').filter(Boolean) || []
    const next = current.includes(answer)
      ? current.filter(item => item !== answer)
      : [...current, answer].sort()
    selectedAnswers.value = { ...selectedAnswers.value, [currentQuestionId.value]: next.join('') }
    return
  }
  selectedAnswers.value = { ...selectedAnswers.value, [currentQuestionId.value]: answer }
}

function updateTextAnswer(event: Event) {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  selectedAnswers.value = { ...selectedAnswers.value, [currentQuestionId.value]: target.value }
}

function checkAnswer(): boolean {
  if (!currentQuestion.value) return false
  const selected = selectedAnswers.value[currentQuestionId.value]
  const answer = currentQuestion.value.answer

  if (typeof answer === 'boolean') {
    return normalizeAnswer(selected) === normalizeAnswer(answer ? '正确' : '错误')
      || normalizeAnswer(selected) === normalizeAnswer(String(answer))
  }
  if (Array.isArray(answer)) {
    return normalizeAnswer(selected) === normalizeAnswer(answer.join(''))
  }
  return normalizeAnswer(selected) === normalizeAnswer(answer)
}

function submitAnswer() {
  if (!currentQuestion.value || showResult.value || !currentAnswer.value.trim()) return
  showResult.value = true
  answeredCount.value += 1

  const isCorrect = checkAnswer()
  if (isCorrect) {
    correctCount.value += 1
  } else {
    saveMistake()
  }
  
  answerRecords.value[currentQuestionIndex.value] = {
    question: currentQuestion.value,
    userAnswer: currentAnswer.value,
    isCorrect
  }
}

async function saveMistake() {
  if (!currentQuestion.value) return
  try {
    const userProfile = loadUserProfile()
    await addMistake({
      user_id: userProfile.userId,
      course: props.course.name,
      question_id: String(currentQuestion.value.id),
      question: currentQuestion.value.question,
      type: currentQuestion.value.type,
      chapter: currentQuestion.value.chapter,
      level: currentQuestion.value.level || '',
      options: currentQuestion.value.options || null,
      answer: currentAnswer.value,
      correct_answer: String(currentQuestion.value.answer),
      analysis: currentQuestion.value.analysis,
      topic: currentQuestion.value.chapter,
    })
  } catch (e) {
    console.error('保存错题失败:', e)
  }
}

function nextQuestion() {
  if (currentQuestionIndex.value < questions.value.length - 1) {
    currentQuestionIndex.value += 1
    showResult.value = false
  } else {
    showCompletion.value = true
  }
}

function resetAndSelect() {
  quizStarted.value = false
  showCompletion.value = false
  currentQuestionIndex.value = 0
  answeredCount.value = 0
  correctCount.value = 0
  selectedAnswers.value = {}
  answerRecords.value = []
  questions.value = []
}

function prevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value -= 1
    showResult.value = false
  }
}

function toggleChapter(chapterId: string) {
  const index = selectedChapterIds.value.indexOf(chapterId)
  if (index === -1) {
    selectedChapterIds.value.push(chapterId)
  } else {
    selectedChapterIds.value.splice(index, 1)
  }
}

function toggleQuestionType(type: string) {
  const index = questionTypes.value.indexOf(type)
  if (index === -1) {
    questionTypes.value.push(type)
  } else {
    questionTypes.value.splice(index, 1)
  }
}

function getQuestionTypeLabel(type: string) {
  switch (type) {
    case 'single': return '单选题'
    case 'multiple': return '多选题'
    case 'judge': return '判断题'
    case 'fill': return '填空题'
    case 'short': return '简答题'
    default: return type
  }
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
  const selectedValue = selectedAnswers.value[currentQuestionId.value] || ''
  const selected = currentQuestion.value.type === 'multiple'
    ? selectedValue.includes(optionLabel)
    : selectedValue === optionLabel
  if (!showResult.value) return selected ? 'option-selected' : ''

  const correct = Array.isArray(currentQuestion.value.answer)
    ? currentQuestion.value.answer.map(String).includes(optionLabel)
    : normalizeAnswer(optionLabel) === normalizeAnswer(currentQuestion.value.answer)
  if (correct) return 'option-correct'
  if (selected && !correct) return 'option-wrong'
  return 'option-muted'
}



</script>

<template>
  <div class="quiz-page">
    <section v-if="!quizStarted" class="quiz-shell">
      <header class="quiz-header">
        <div>
          <h1>{{ course.name }} - 生成练习题</h1>
          <p>选择章节和题型，生成个性化练习题</p>
        </div>
        <div class="quiz-header-actions">
          <button type="button" title="返回详情" @click="emit('navigate', 'detail')">↩</button>
          <button type="button" title="退出练习" @click="emit('navigate', 'courses')">×</button>
        </div>
      </header>

      <div v-if="loading" class="quiz-loading">
        <div></div>
        <strong>AI 正在生成《{{ course.name }}》练习题</strong>
        <p>会根据您选择的章节和题型生成分层题目。</p>
      </div>

      <div v-else-if="course.chapters?.length" class="chapter-selector">
        <div class="selector-row">
          <div class="selector-group">
            <h3>选择章节（可多选）</h3>
            <div class="chapter-tags">
              <button
                class="chapter-tag"
                :class="{ active: selectedChapterIds.length === 0 }"
                @click="selectedChapterIds = []"
              >
                全部章节
              </button>
              <button
                v-for="chapter in course.chapters"
                :key="chapter.id"
                class="chapter-tag"
                :class="{ active: selectedChapterIds.includes(String(chapter.id)) }"
                @click="toggleChapter(String(chapter.id))"
              >
                {{ chapter.name }}
              </button>
            </div>
          </div>
          
          <div class="selector-group">
            <h3>选择题型（可多选）</h3>
            <div class="chapter-tags">
              <button
                class="chapter-tag"
                :class="{ active: questionTypes.length === 0 }"
                @click="questionTypes = []"
              >
                全部题型
              </button>
              <button
                v-for="type in allQuestionTypes"
                :key="type.value"
                class="chapter-tag"
                :class="{ active: questionTypes.includes(type.value) }"
                @click="toggleQuestionType(type.value)"
              >
                {{ type.label }}
              </button>
            </div>
          </div>
        </div>

        <div class="selection-summary">
          <span>已选择：{{ selectedChapterIds.length === 0 ? '全部章节' : ` ${selectedChapterIds.length} 个章节` }} · {{ questionTypes.length === 0 ? '全部题型' : questionTypes.map(t => allQuestionTypes.find(qt => qt.value === t)?.label || t).join('、') }}</span>
        </div>
        
        <button class="regenerate-btn" :disabled="loading" @click="generateAiQuestions">
          生成练习题
        </button>
      </div>
    </section>

    <section v-else class="quiz-shell">
      <header class="quiz-header">
        <div>
          <h1>{{ course.name }}测试题</h1>
          <p>答对 {{ correctCount }} 题 · 已答 {{ answeredCount }} 题 · 正确率 {{ accuracy }}%</p>
        </div>
        <div class="quiz-header-actions">
          <button type="button" title="重新选择" @click="resetAndSelect">↺</button>
          <button type="button" title="返回详情" @click="emit('navigate', 'detail')">↩</button>
          <button type="button" title="退出练习" @click="emit('navigate', 'courses')">×</button>
        </div>
      </header>

      <div class="quiz-progress">
        <div class="progress-segments">
          <span
            v-for="(_, index) in questions"
            :key="index"
            :class="{ active: index <= currentQuestionIndex, answered: index < currentQuestionIndex || (index === currentQuestionIndex && showResult) }"
          ></span>
        </div>
        <b>{{ questions.length ? currentQuestionIndex + 1 : 0 }} / {{ questions.length || 1 }}</b>
      </div>

      <div v-if="showCompletion" class="completion-state">
        <h2>练习完成！</h2>
        <div class="completion-score">
          <div class="score-circle">
            <span class="score-value">{{ accuracy }}</span>
            <span class="score-unit">分</span>
          </div>
          <div class="score-details">
            <p>答对 {{ correctCount }} 题</p>
            <p>答错 {{ answeredCount - correctCount }} 题</p>
            <p>共 {{ answeredCount }} 题</p>
          </div>
        </div>
        <p class="completion-feedback">
          {{ correctCount === answeredCount 
            ? '太棒了！全部答对，继续保持！' 
            : (correctCount >= answeredCount * 0.8 
              ? '表现优秀！再接再厉！' 
              : (correctCount >= answeredCount * 0.6 
                ? '表现不错，继续加油！' 
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
                    <span class="value correct">{{ record.question.answer }}</span>
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
          <button class="primary-button" @click="resetAndSelect">重新选择</button>
          <button class="ghost-button" @click="emit('navigate', 'detail')">返回详情</button>
        </div>
      </div>

      <article v-else-if="currentQuestion" class="quiz-card">
        <div v-if="generationError" class="quiz-warning">{{ generationError }}</div>

        <div class="question-meta">
          <span>{{ currentQuestion.chapter }}</span>
          <span>{{ getQuestionTypeLabel(currentQuestion.type) }}</span>
        </div>

        <div class="question-stack">
          <h2>第 {{ currentQuestionIndex + 1 }} 题</h2>
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
            :value="currentAnswer"
            :disabled="showResult"
            rows="5"
            class="answer-input"
            placeholder="请输入你的答案"
            @input="updateTextAnswer"
          ></textarea>

          <input
            v-else
            :value="currentAnswer"
            :disabled="showResult"
            class="answer-input"
            placeholder="请输入答案"
            @input="updateTextAnswer"
          />

          <details class="question-hint">
            <summary>提示</summary>
            <p>先判断题目考查的概念，再排除明显不符合定义的选项。</p>
          </details>
        </div>

        <div v-if="showResult" :class="['result-panel', checkAnswer() ? 'result-correct' : 'result-wrong']">
          <strong>{{ checkAnswer() ? '回答正确' : '回答错误' }}</strong>
          <p>参考答案：{{ currentQuestion.answer }}</p>
          <p>{{ currentQuestion.analysis }}</p>
        </div>

        <footer class="quiz-footer">
          <button type="button" class="ghost-button" :disabled="currentQuestionIndex === 0" @click="prevQuestion">
            上一个
          </button>
          <button
            v-if="!showResult"
            type="button"
            class="primary-button"
            :disabled="!currentAnswer.trim()"
            @click="submitAnswer"
          >
            提交
          </button>
          <button
            v-else-if="currentQuestionIndex < questions.length - 1"
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
    </section>
  </div>
</template>

<style scoped>
.quiz-page {
  min-height: calc(100vh - 72px);
  padding: 10px;
  background: #fff;
  color: #202123;
}

.quiz-shell {
  position: relative;
  overflow: hidden;
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
  box-shadow: 0 18px 48px rgba(52, 42, 120, .08);
}
.quiz-shell::before { content: ""; position: absolute; top: 0; right: 8%; left: 8%; height: 2px; background: linear-gradient(90deg, transparent, #c8c1ff, #6d5de7, #c8c1ff, transparent); opacity: .75; }

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
  background: #c8c1ff;
  transform: scaleY(1.25);
}

.progress-segments span.answered {
  background: linear-gradient(90deg, #5146cf, #8b7df0);
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
  position: relative;
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 50%;
  background: conic-gradient(from 20deg, #5146cf, #aa9fff, #eeeaff, #5146cf);
  box-shadow: 0 0 28px rgba(109,93,231,.25);
  animation: spin 1.15s linear infinite, aiOrbPulse 2s ease-in-out infinite;
}
.quiz-loading div::after { content: ""; position: absolute; inset: 6px; border-radius: inherit; background: #fff; }

.quiz-loading strong {
  color: #111827;
}

.quiz-loading p {
  margin: 0;
  color: #8b8f98;
}

.quiz-card {
  width: min(760px, 100%);
  justify-self: center;
  display: grid;
  align-content: start;
  gap: 22px;
  animation: quizCardIn .38s cubic-bezier(.16,1,.3,1) both;
}

.quiz-warning {
  padding: 12px 14px;
  border: 1px solid #f6d58a;
  border-radius: 14px;
  color: #8a5a00;
  background: #fff8e7;
  font-size: 13px;
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
  animation: optionIn .32s cubic-bezier(.16,1,.3,1) both;
}
.exercise-option:nth-child(2) { animation-delay: 45ms; }
.exercise-option:nth-child(3) { animation-delay: 90ms; }
.exercise-option:nth-child(4) { animation-delay: 135ms; }

.exercise-option:hover:not(:disabled),
.option-selected {
  border-color: #9f94f2;
  background: #f8f7ff;
  box-shadow: 0 8px 24px rgba(81,70,207,.09);
  transform: translateY(-2px);
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
  border-color: #9f94f2;
  box-shadow: 0 0 0 4px rgba(109,93,231,.1);
}

.question-hint {
  width: fit-content;
  color: #4b5563;
  font-size: 14px;
}

.question-hint summary {
  cursor: pointer;
  font-weight: 700;
}

.question-hint p {
  max-width: 560px;
  margin: 10px 0 0;
  color: #6b7280;
  line-height: 1.65;
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
  background: linear-gradient(110deg, #433aa8, #6d5de7, #5146cf);
  background-size: 180% 100%;
  box-shadow: 0 8px 20px rgba(81,70,207,.18);
}
.primary-button:hover:not(:disabled) { background-position: 100% 0; transform: translateY(-1px); box-shadow: 0 11px 26px rgba(81,70,207,.25); }

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

@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes aiOrbPulse {
  0%, 100% { filter: saturate(.9); }
  50% { filter: saturate(1.35); box-shadow: 0 0 38px rgba(109,93,231,.38); }
}
@keyframes quizCardIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes optionIn {
  from { opacity: 0; transform: translateY(7px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  .quiz-card, .exercise-option, .quiz-loading div { animation: none; }
}

.chapter-selector {
  width: min(960px, 100%);
  justify-self: center;
  background: #fff;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,.05);
  border: 1px solid #f0f0f0;
}

.selector-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}

.selector-group h3 {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 700;
  color: #374151;
}

.chapter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chapter-tag {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  background: #fff;
  color: #4b5563;
  font-size: 13px;
  cursor: pointer;
  transition: all .2s ease;
}

.chapter-tag:hover {
  border-color: #9f94f2;
  color: #5146cf;
  background: #f8f7ff;
  transform: translateY(-1px);
}

.chapter-tag.active {
  background: #5146cf;
  border-color: #5146cf;
  color: #fff;
  box-shadow: 0 6px 16px rgba(81,70,207,.2);
}

.selection-summary {
  padding: 12px 16px;
  margin-top: 8px;
  border-radius: 10px;
  border: 1px solid #ece9ff;
  background: #faf9ff;
  color: #6b7280;
  font-size: 13px;
}

.regenerate-btn {
  width: 100%;
  padding: 12px;
  margin-top: 16px;
  background: linear-gradient(110deg, #433aa8 0%, #6d5de7 48%, #5146cf 100%);
  background-size: 200% 100%;
  color: #fff;
  border: 0;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 9px 24px rgba(81,70,207,.2);
  transition: background-position .35s ease, transform .2s ease, box-shadow .2s ease;
}

.regenerate-btn:hover:not(:disabled) {
  background-position: 100% 0;
  transform: translateY(-2px);
  box-shadow: 0 13px 30px rgba(81,70,207,.28);
}

.regenerate-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.answer-details {
  width: min(760px, 100%);
  margin: 20px auto 0;
  text-align: left;
}

.answer-details h3 {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
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
  border: 1px solid #e5e7eb;
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

@media (max-width: 760px) {
  .quiz-page { padding: 0; }
  .quiz-shell { min-height: calc(100vh - 64px); padding: 22px 16px; border-radius: 0; border-left: 0; border-right: 0; }
  .quiz-header, .quiz-footer { align-items: flex-start; }
  .quiz-card { width: 100%; }
  .question-stack > p { font-size: 16px; }
  .exercise-option { min-height: 58px; padding: 15px 16px; font-size: 15px; }
  .chapter-selector { padding: 20px; }
}
</style>
