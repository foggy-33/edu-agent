<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { loadUserProfile } from '../api/userProfile'
import { listAllMistakes, listMistakes, markMistakeMastered, markMistakeMasteredAny } from '../api/client'
import type { Question } from '../types'

const props = defineProps<{
  course: { id: string | number; name: string }
}>()

const emit = defineEmits<{
  navigate: [page: 'courses' | 'detail' | 'exercise']
}>()

const mistakes = ref<Question[]>([])
const loading = ref(false)
const currentIndex = ref(0)
const selectedAnswers = ref<Record<string, string>>({})
const showResult = ref(false)
const masteredCount = ref(0)
const currentTab = ref<'unmastered' | 'mastered'>('unmastered')
const unmasteredCount = ref(0)
const masteredTotalCount = ref(0)

const currentQuestion = computed(() => mistakes.value[currentIndex.value])

const progressText = computed(() => {
  return `${currentIndex.value + 1} / ${mistakes.value.length}`
})

async function loadMistakes() {
  loading.value = true
  try {
    const userProfile = loadUserProfile()
    const isMastered = currentTab.value === 'mastered'
    // 如果是全部错题入口，获取所有课程的错题
    if (props.course.name === '全部错题') {
      const response = await listAllMistakes(userProfile.userId, isMastered)
      mistakes.value = response.mistakes || []
    } else {
      // 否则获取当前课程的错题
      const response = await listMistakes(userProfile.userId, props.course.name)
      mistakes.value = (response.mistakes || []).filter(m => (m as any).mastered === isMastered)
    }
    currentIndex.value = 0
    showResult.value = false
  } catch {
    mistakes.value = []
  } finally {
    loading.value = false
  }
}

function switchTab(tab: 'unmastered' | 'mastered') {
  currentTab.value = tab
  loadMistakes()
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

  if (checkAnswer()) {
    masteredCount.value++
    const userProfile = loadUserProfile()
    const q = currentQuestion.value as any
    // 使用 question_id 字段（后端保存的字段），而不是 id 字段
    const questionId = q.question_id !== undefined ? String(q.question_id) : String(q.id)
    // 如果是全部错题入口，使用跨课程标记掌握
    if (props.course.name === '全部错题') {
      await markMistakeMasteredAny(userProfile.userId, questionId)
    } else {
      await markMistakeMastered(userProfile.userId, props.course.name, questionId)
    }
    // 标记当前题已掌握，点击下一题时移除
    (currentQuestion.value as any).justMastered = true
  }
}

function nextQuestion() {
  // 如果当前题刚答对，先移除它，索引不变（因为列表变短了，当前位置就是下一题）
  if ((currentQuestion.value as any)?.justMastered) {
    mistakes.value.splice(currentIndex.value, 1)
    // 如果移除后列表为空，切换到已掌握
    if (mistakes.value.length === 0) {
      switchTab('mastered')
      return
    }
    // 如果当前索引超出范围，回退到最后一题
    if (currentIndex.value >= mistakes.value.length) {
      currentIndex.value = mistakes.value.length - 1
    }
    showResult.value = false
  } else if (currentIndex.value < mistakes.value.length - 1) {
    // 答错了，正常切换到下一题
    currentIndex.value++
    showResult.value = false
  } else {
    // 最后一题且答错，刷新列表
    loadMistakes()
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
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

onMounted(loadMistakes)
</script>

<template>
  <div class="mistake-book-page">
    <section class="quiz-shell">
      <header class="quiz-header">
        <div>
          <h1>{{ course.name }} - 错题本</h1>
          <p>{{ currentTab === 'unmastered' ? '待复习' : '已掌握' }}：{{ mistakes.length }} 题</p>
        </div>
        <div class="quiz-header-actions">
          <button type="button" title="返回详情" @click="emit('navigate', 'detail')">↩</button>
          <button type="button" title="退出" @click="emit('navigate', 'courses')">×</button>
        </div>
      </header>

      <div class="mistake-tabs">
        <button
          type="button"
          :class="['tab-button', currentTab === 'unmastered' ? 'tab-active unmastered' : '']"
          @click="switchTab('unmastered')"
        >
          未掌握
        </button>
        <button
          type="button"
          :class="['tab-button', currentTab === 'mastered' ? 'tab-active mastered' : '']"
          @click="switchTab('mastered')"
        >
          已掌握
        </button>
      </div>

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
          <button v-else type="button" class="primary-button" @click="emit('navigate', 'detail')">
            完成
          </button>
        </footer>
      </article>
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
