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

const exerciseProgress = computed(() => {
  return questions.value.length > 0
    ? ((currentQuestionIndex.value + 1) / questions.value.length) * 100
    : 0
})

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
  const selected = selectedAnswers.value[currentQuestionId.value] === optionLabel
  if (!showResult.value) return selected ? 'option-selected' : ''

  const correct = normalizeAnswer(optionLabel) === normalizeAnswer(currentQuestion.value.answer)
  if (correct) return 'option-correct'
  if (selected && !correct) return 'option-wrong'
  return 'option-muted'
}

onMounted(generateAiQuestions)
</script>

<template>
  <div class="space-y-6">
    <section class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 bg-gray-100 border border-gray-200 rounded-xl flex items-center justify-center text-sm font-bold text-gray-700">
            {{ course.icon }}
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ course.name }} · AI 练习</h1>
            <div class="text-gray-500">第 {{ currentQuestionIndex + 1 }} / {{ questions.length || 1 }} 题</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button @click="emit('navigate', 'detail')" class="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 rounded-xl font-medium transition-all">
            返回详情
          </button>
          <button @click="emit('navigate', 'courses')" class="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 rounded-xl font-medium transition-all">
            退出练习
          </button>
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
        <div class="text-3xl font-bold text-gray-900 text-center">{{ questions.length }}</div>
        <div class="text-sm text-gray-500 text-center mt-1">题目总数</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
        <div class="text-3xl font-bold text-blue-600 text-center">{{ answeredCount }}</div>
        <div class="text-sm text-gray-500 text-center mt-1">已答题目</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
        <div class="text-3xl font-bold text-green-600 text-center">{{ correctCount }}</div>
        <div class="text-sm text-gray-500 text-center mt-1">答对题目</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
        <div class="text-3xl font-bold text-amber-600 text-center">{{ accuracy }}%</div>
        <div class="text-sm text-gray-500 text-center mt-1">正确率</div>
      </div>
    </div>

    <section class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div v-if="loading" class="py-20 text-center">
        <div class="mx-auto mb-5 h-10 w-10 rounded-full border-2 border-gray-200 border-t-gray-900 animate-spin"></div>
        <h2 class="text-lg font-semibold text-gray-900">AI 正在生成《{{ course.name }}》练习题</h2>
        <p class="text-sm text-gray-500 mt-2">会根据课程章节、学习建议和当前模型配置生成分层题目。</p>
      </div>

      <div v-else-if="currentQuestion" class="space-y-6">
        <div v-if="generationError" class="rounded-xl bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 text-sm">
          {{ generationError }}
        </div>

        <div class="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div class="h-full bg-gray-900 rounded-full transition-all duration-500" :style="{ width: exerciseProgress + '%' }"></div>
        </div>

        <div class="flex items-center gap-3 flex-wrap">
          <span class="px-4 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
            {{ currentQuestion.chapter }}
          </span>
          <span class="px-4 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
            {{ getQuestionTypeLabel(currentQuestion.type) }}
          </span>
        </div>

        <div class="bg-gray-50 rounded-xl p-6">
          <div class="text-xl font-medium text-gray-900 leading-relaxed">{{ currentQuestion.question }}</div>
        </div>

        <div v-if="currentQuestion.type === 'single' || currentQuestion.type === 'judge'" class="space-y-3">
          <button
            v-for="option in optionsFor(currentQuestion)"
            :key="option.label"
            @click="selectAnswer(option.label)"
            :disabled="showResult"
            :class="['exercise-option', getOptionClass(option.label)]"
          >
            <span>{{ option.label }}</span>
            {{ option.text }}
          </button>
        </div>

        <textarea
          v-else-if="currentQuestion.type === 'short'"
          :value="currentAnswer"
          :disabled="showResult"
          rows="4"
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

        <div v-if="showResult" :class="['result-panel', checkAnswer() ? 'result-correct' : 'result-wrong']">
          <div class="font-bold text-lg">{{ checkAnswer() ? '回答正确' : '回答错误' }}</div>
          <p class="mt-2">参考答案：{{ currentQuestion.answer }}</p>
          <p class="mt-2 leading-relaxed">{{ currentQuestion.analysis }}</p>
        </div>

        <div class="flex items-center justify-between pt-6 border-t border-gray-100">
          <button
            @click="prevQuestion"
            :disabled="currentQuestionIndex === 0"
            class="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一题
          </button>

          <div class="flex-1 flex justify-center">
            <button
              v-if="!showResult"
              @click="submitAnswer"
              :disabled="!currentAnswer.trim()"
              class="px-8 py-3 bg-gray-900 text-white font-medium rounded-xl hover:bg-black transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              提交答案
            </button>
            <button
              v-else-if="currentQuestionIndex < questions.length - 1"
              @click="nextQuestion"
              class="px-8 py-3 bg-gray-900 text-white font-medium rounded-xl hover:bg-black transition-all shadow-sm"
            >
              下一题
            </button>
            <button
              v-else
              @click="emit('navigate', 'detail')"
              class="px-8 py-3 bg-green-600 text-white font-medium rounded-xl hover:bg-green-700 transition-all shadow-sm"
            >
              完成练习
            </button>
          </div>

          <button
            @click="nextQuestion"
            :disabled="currentQuestionIndex === questions.length - 1 || !showResult"
            class="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一题
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.exercise-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  color: #374151;
  background: #fff;
  text-align: left;
  transition: all .2s ease;
}

.exercise-option:hover:not(:disabled),
.option-selected {
  border-color: #111827;
  background: #f9fafb;
}

.exercise-option span {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #f3f4f6;
  color: #111827;
  font-weight: 700;
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
  opacity: .55;
}

.answer-input {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #d1d5db;
  border-radius: 14px;
  outline: 0;
  resize: vertical;
  color: #111827;
  background: #fff;
}

.answer-input:focus {
  border-color: #111827;
}

.result-panel {
  padding: 18px;
  border-radius: 14px;
  border: 1px solid;
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
</style>
