<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { generateLearningResources } from '../api/client'
import { loadSiliconFlowConfig } from '../api/settings'
import { loadUserProfile } from '../api/userProfile'
import type { CollaborativeExerciseItem, Course, Question } from '../types'

const props = defineProps<{
  course: Course
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

const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])
const currentQuestionId = computed(() => String(currentQuestion.value?.id || ''))

const accuracy = computed(() => {
  return answeredCount.value > 0
    ? Math.round((correctCount.value / answeredCount.value) * 100)
    : 0
})

const currentAnswer = computed(() => selectedAnswers.value[currentQuestionId.value] || '')

function currentChapterNames() {
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

function fallbackQuestions() {
  return props.course.questions.length ? props.course.questions : [
    {
      id: `${props.course.id}-fallback`,
      type: 'short',
      chapter: props.course.name,
      question: `请概括《${props.course.name}》当前阶段最重要的三个知识点，并说明它们之间的关系。`,
      options: [],
      answer: '围绕核心概念、适用条件和典型应用进行说明。',
      analysis: '开放题重点检查是否覆盖核心概念、适用条件、典型应用，以及知识点之间的联系。',
    },
  ]
}

async function generateAiQuestions() {
  loading.value = true
  generationError.value = ''
  questions.value = []
  try {
    const config = loadSiliconFlowConfig()
    const userProfile = loadUserProfile()
    const result = await generateLearningResources({
      user_id: userProfile.userId,
      major: userProfile.major || '计算机类',
      course: props.course.name,
      chapter: currentChapterNames(),
      weakness: props.course.suggestions?.join('；') || props.course.description || props.course.name,
      goal: `针对《${props.course.name}》生成可直接作答的分层练习题`,
      resourceTypes: ['exercise'],
      fileIds: [],
      ...config,
    })
    questions.value = result.exerciseItems?.length
      ? result.exerciseItems.map(toQuestion)
      : fallbackQuestions()
  } catch (reason) {
    generationError.value = reason instanceof Error ? reason.message : 'AI 生成练习题失败，已使用课程基础题'
    questions.value = fallbackQuestions()
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
  if (checkAnswer()) correctCount.value += 1
}

function nextQuestion() {
  if (currentQuestionIndex.value < questions.value.length - 1) {
    currentQuestionIndex.value += 1
    showResult.value = false
  }
}

function prevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value -= 1
    showResult.value = false
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

onMounted(generateAiQuestions)
</script>

<template>
  <div class="quiz-page">
    <section class="quiz-shell">
      <header class="quiz-header">
        <div>
          <h1>{{ course.name }}测试题</h1>
          <p>答对 {{ correctCount }} 题 · 已答 {{ answeredCount }} 题 · 正确率 {{ accuracy }}%</p>
        </div>
        <div class="quiz-header-actions">
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

      <div v-if="loading" class="quiz-loading">
        <div></div>
        <strong>AI 正在生成《{{ course.name }}》练习题</strong>
        <p>会根据课程章节、学习建议和当前模型配置生成分层题目。</p>
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
          <button v-else type="button" class="primary-button" @click="emit('navigate', 'detail')">
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 760px) {
  .quiz-page { padding: 0; }
  .quiz-shell { min-height: calc(100vh - 64px); padding: 22px 16px; border-radius: 0; border-left: 0; border-right: 0; }
  .quiz-header, .quiz-footer { align-items: flex-start; }
  .quiz-card { width: 100%; }
  .question-stack > p { font-size: 16px; }
  .exercise-option { min-height: 58px; padding: 15px 16px; font-size: 15px; }
}
</style>
