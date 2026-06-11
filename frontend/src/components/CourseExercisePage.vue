<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Course, Question } from '../types'

const props = defineProps<{
  course: Course
}>()

const emit = defineEmits<{
  navigate: [page: 'courses' | 'detail']
}>()

const currentQuestionIndex = ref(0)
const selectedAnswers = ref<Record<number, string | string[] | boolean>>({})
const showResult = ref(false)
const answeredCount = ref(0)
const correctCount = ref(0)

const currentQuestions = computed(() => props.course.questions || [])
const currentQuestion = computed(() => currentQuestions.value[currentQuestionIndex.value])

const exerciseProgress = computed(() => {
  return currentQuestions.value.length > 0 
    ? ((currentQuestionIndex.value + 1) / currentQuestions.value.length) * 100 
    : 0
})

const accuracy = computed(() => {
  return answeredCount.value > 0 
    ? Math.round((correctCount.value / answeredCount.value) * 100) 
    : 0
})

function resetExercise() {
  currentQuestionIndex.value = 0
  selectedAnswers.value = {}
  showResult.value = false
  answeredCount.value = 0
  correctCount.value = 0
}

function selectAnswer(answer: string) {
  if (showResult.value || !currentQuestion.value) return
  
  const question = currentQuestion.value
  if (question.type === 'multiple') {
    const current = (selectedAnswers.value[question.id] as string[]) || []
    if (current.includes(answer)) {
      selectedAnswers.value[question.id] = current.filter(a => a !== answer)
    } else {
      selectedAnswers.value[question.id] = [...current, answer].sort()
    }
  } else if (question.type === 'judge') {
    selectedAnswers.value[question.id] = answer === 'true'
  } else {
    selectedAnswers.value[question.id] = answer
  }
}

function submitAnswer() {
  showResult.value = true
  answeredCount.value++
  
  const correct = checkAnswer()
  if (correct) correctCount.value++
}

function checkAnswer(): boolean {
  if (!currentQuestion.value) return false
  
  const current = currentQuestion.value
  const selected = selectedAnswers.value[current.id]
  
  if (current.type === 'multiple') {
    const correctAnswer = current.answer as string[]
    const selectedArray = selected as string[] || []
    return JSON.stringify(correctAnswer.sort()) === JSON.stringify(selectedArray.sort())
  }
  if (current.type === 'judge') {
    return selected === current.answer
  }
  return selected === current.answer
}

function nextQuestion() {
  if (currentQuestionIndex.value < currentQuestions.value.length - 1) {
    currentQuestionIndex.value++
    showResult.value = false
  }
}

function prevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    showResult.value = false
  }
}

function getQuestionTypeLabel(type: string) {
  switch (type) {
    case 'single': return '单选题'
    case 'multiple': return '多选题'
    case 'judge': return '判断题'
    default: return type
  }
}

function getQuestionTypeClass(type: string) {
  switch (type) {
    case 'single': return 'bg-blue-100 text-blue-700'
    case 'multiple': return 'bg-green-100 text-green-700'
    case 'judge': return 'bg-purple-100 text-purple-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

function getOptionClass(option: { label: string }) {
  if (!showResult.value || !currentQuestion.value) {
    const question = currentQuestion.value!
    if (question.type === 'multiple') {
      const selected = (selectedAnswers.value[question.id] as string[]) || []
      return selected.includes(option.label)
        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
        : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
    } else if (question.type === 'judge') {
      const selected = selectedAnswers.value[question.id] as boolean
      const isTrue = option.label === 'true'
      return selected === isTrue
        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
        : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
    }
    return selectedAnswers.value[question.id] === option.label
      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
      : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
  }
  
  const question = currentQuestion.value!
  const isCorrect = question.type === 'multiple'
    ? (question.answer as string[]).includes(option.label)
    : question.type === 'judge'
      ? (option.label === 'true') === question.answer
      : option.label === question.answer
  
  const isSelected = question.type === 'multiple'
    ? ((selectedAnswers.value[question.id] as string[]) || []).includes(option.label)
    : question.type === 'judge'
      ? ((selectedAnswers.value[question.id] as boolean) === (option.label === 'true'))
      : selectedAnswers.value[question.id] === option.label
  
  if (isCorrect) return 'border-green-500 bg-green-50 text-green-700'
  if (isSelected && !isCorrect) return 'border-red-500 bg-red-50 text-red-700'
  return 'border-gray-200 opacity-50'
}
</script>

<template>
  <div class="space-y-6">
    <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-xl">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center text-3xl">
            {{ course.icon }}
          </div>
          <div>
            <h1 class="text-2xl font-bold">{{ course.name }} - 习题练习</h1>
            <div class="text-white/80">第 {{ currentQuestionIndex + 1 }} / {{ currentQuestions.length }} 题</div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="emit('navigate', 'detail')"
            class="px-5 py-2.5 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-all"
          >
            ← 返回课程详情
          </button>
          <button 
            @click="emit('navigate', 'courses')"
            class="px-5 py-2.5 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-all"
          >
            ✕ 退出练习
          </button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl p-5 shadow-lg">
        <div class="text-3xl font-bold text-gray-800 text-center">{{ currentQuestions.length }}</div>
        <div class="text-sm text-gray-500 text-center mt-1">题目总数</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-lg">
        <div class="text-3xl font-bold text-blue-600 text-center">{{ answeredCount }}</div>
        <div class="text-sm text-gray-500 text-center mt-1">已答题目</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-lg">
        <div class="text-3xl font-bold text-green-600 text-center">{{ correctCount }}</div>
        <div class="text-sm text-gray-500 text-center mt-1">答对题目</div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-lg">
        <div class="text-3xl font-bold text-amber-600 text-center">{{ accuracy }}%</div>
        <div class="text-sm text-gray-500 text-center mt-1">正确率</div>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-lg p-6">
      <div class="h-3 bg-gray-200 rounded-full overflow-hidden mb-8">
        <div
          class="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
          :style="{ width: exerciseProgress + '%' }"
        ></div>
      </div>

      <div v-if="currentQuestion" class="space-y-6">
        <div class="flex items-center gap-3 flex-wrap">
          <span class="px-4 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
            {{ currentQuestion.chapter }}
          </span>
          <span :class="['px-4 py-1.5 rounded-full text-sm font-medium', getQuestionTypeClass(currentQuestion.type)]">
            {{ getQuestionTypeLabel(currentQuestion.type) }}
          </span>
        </div>

        <div class="bg-gray-50 rounded-xl p-6">
          <div class="text-xl font-medium text-gray-800">{{ currentQuestion.question }}</div>
        </div>

        <div v-if="currentQuestion.type !== 'judge'" class="space-y-3">
          <button
            v-for="option in currentQuestion.options"
            :key="option.label"
            @click="selectAnswer(option.label)"
            :disabled="showResult"
            :class="[
              'w-full p-4 rounded-xl border-2 text-left transition-all',
              getOptionClass(option)
            ]"
          >
            <span class="font-medium mr-3 text-lg">{{ option.label }}.</span>
            {{ option.text }}
          </button>
        </div>

        <div v-else class="grid grid-cols-2 gap-4">
          <button
            @click="selectAnswer('true')"
            :disabled="showResult"
            :class="[
              'p-6 rounded-xl border-2 transition-all text-center',
              getOptionClass({ label: 'true' })
            ]"
          >
            <div class="text-3xl mb-2">✅</div>
            <div class="font-medium text-lg">正确</div>
          </button>
          <button
            @click="selectAnswer('false')"
            :disabled="showResult"
            :class="[
              'p-6 rounded-xl border-2 transition-all text-center',
              getOptionClass({ label: 'false' })
            ]"
          >
            <div class="text-3xl mb-2">❌</div>
            <div class="font-medium text-lg">错误</div>
          </button>
        </div>

        <div v-if="showResult" class="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <div class="flex items-center gap-3 mb-4">
            <span class="text-2xl">💡</span>
            <span class="font-bold text-lg text-amber-800">答案解析</span>
          </div>
          <p class="text-amber-700 text-lg leading-relaxed">{{ currentQuestion.analysis }}</p>
        </div>

        <div class="flex items-center justify-between pt-6 border-t border-gray-100">
          <button
            @click="prevQuestion"
            :disabled="currentQuestionIndex === 0"
            class="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← 上一题
          </button>
          
          <div class="flex-1 flex justify-center">
            <button
              v-if="!showResult"
              @click="submitAnswer"
              class="px-8 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all shadow-lg"
            >
              提交答案
            </button>
            <button
              v-else-if="currentQuestionIndex < currentQuestions.length - 1"
              @click="nextQuestion"
              class="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg"
            >
              下一题 →
            </button>
            <button
              v-else
              @click="emit('navigate', 'detail')"
              class="px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium rounded-xl hover:from-amber-600 hover:to-orange-700 transition-all shadow-lg"
            >
              🎉 完成练习
            </button>
          </div>

          <button
            @click="nextQuestion"
            :disabled="currentQuestionIndex === currentQuestions.length - 1 || !showResult"
            class="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一题 →
          </button>
        </div>
      </div>

      <div v-else class="text-center py-16">
        <div class="text-6xl mb-4">📭</div>
        <div class="text-gray-500 text-lg">暂无习题</div>
      </div>
    </div>
  </div>
</template>
