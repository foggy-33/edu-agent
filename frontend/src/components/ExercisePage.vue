<script setup lang="ts">
import { ref, computed } from 'vue'

const questions = ref([
  {
    id: 1,
    type: 'single',
    subject: '数据库系统',
    chapter: '关系模型',
    question: '以下哪个是关系数据库的基本操作？',
    options: [
      { label: 'A', text: '插入(Insert)' },
      { label: 'B', text: '排序(Sort)' },
      { label: 'C', text: '合并(Merge)' },
      { label: 'D', text: '哈希(Hash)' }
    ],
    answer: 'A',
    analysis: '关系数据库的基本操作包括：选择(Select)、投影(Project)、连接(Join)、插入(Insert)、删除(Delete)、更新(Update)等。'
  },
  {
    id: 2,
    type: 'single',
    subject: '数据结构',
    chapter: '树与二叉树',
    question: '一棵完全二叉树有100个节点，则它的叶子节点数是？',
    options: [
      { label: 'A', text: '49' },
      { label: 'B', text: '50' },
      { label: 'C', text: '51' },
      { label: 'D', text: '52' }
    ],
    answer: 'B',
    analysis: '完全二叉树的性质：若节点总数为n，则叶子节点数为(n+1)/2向下取整或n/2向上取整。100个节点时，叶子节点数为50。'
  },
  {
    id: 3,
    type: 'multiple',
    subject: '操作系统',
    chapter: '进程管理',
    question: '以下哪些是进程调度算法？',
    options: [
      { label: 'A', text: 'FCFS(先来先服务)' },
      { label: 'B', text: 'SJF(短作业优先)' },
      { label: 'C', text: 'LRU(最近最少使用)' },
      { label: 'D', text: 'RR(时间片轮转)' }
    ],
    answer: ['A', 'B', 'D'],
    analysis: 'FCFS、SJF、RR都是进程调度算法。LRU是页面置换算法，不是进程调度算法。'
  },
  {
    id: 4,
    type: 'judge',
    subject: '计算机网络',
    chapter: 'TCP/IP协议',
    question: 'TCP协议是面向连接的可靠传输协议。',
    answer: true,
    analysis: 'TCP(传输控制协议)是面向连接的、可靠的、基于字节流的传输层协议，通过三次握手建立连接，提供数据的可靠传输。'
  },
  {
    id: 5,
    type: 'single',
    subject: '算法设计',
    chapter: '动态规划',
    question: '动态规划算法通常适用于具有什么性质的问题？',
    options: [
      { label: 'A', text: '最优子结构和重叠子问题' },
      { label: 'B', text: '贪心选择性质' },
      { label: 'C', text: '分治性质' },
      { label: 'D', text: '回溯性质' }
    ],
    answer: 'A',
    analysis: '动态规划适用于具有最优子结构（大问题的最优解包含子问题的最优解）和重叠子问题（子问题会被重复计算）性质的问题。'
  }
])

const currentIndex = ref(0)
const selectedAnswers = ref<Record<number, string | string[] | boolean>>({})
const showResult = ref(false)
const answeredCount = ref(0)
const correctCount = ref(0)
const practiceMode = ref<'sequence' | 'random'>('sequence')
const selectedSubject = ref('all')
const selectedChapter = ref('all')

const filteredQuestions = computed(() => {
  let result = questions.value
  if (selectedSubject.value !== 'all') {
    result = result.filter(q => q.subject === selectedSubject.value)
  }
  if (selectedChapter.value !== 'all') {
    result = result.filter(q => q.chapter === selectedChapter.value)
  }
  return practiceMode.value === 'random' 
    ? [...result].sort(() => Math.random() - 0.5) 
    : result
})

const currentQuestion = computed(() => filteredQuestions.value[currentIndex.value])
const progress = computed(() => filteredQuestions.value.length > 0 
  ? ((currentIndex.value + 1) / filteredQuestions.value.length) * 100 
  : 0)

const subjects = computed(() => {
  const set = new Set(questions.value.map(q => q.subject))
  return ['all', ...Array.from(set)]
})

const chapters = computed(() => {
  if (selectedSubject.value === 'all') {
    const set = new Set(questions.value.map(q => q.chapter))
    return ['all', ...Array.from(set)]
  }
  const set = new Set(questions.value
    .filter(q => q.subject === selectedSubject.value)
    .map(q => q.chapter))
  return ['all', ...Array.from(set)]
})

function selectAnswer(answer: string) {
  if (showResult.value) return
  
  if (currentQuestion.value.type === 'multiple') {
    const current = (selectedAnswers.value[currentQuestion.value.id] as string[]) || []
    if (current.includes(answer)) {
      selectedAnswers.value[currentQuestion.value.id] = current.filter(a => a !== answer)
    } else {
      selectedAnswers.value[currentQuestion.value.id] = [...current, answer].sort()
    }
  } else if (currentQuestion.value.type === 'judge') {
    selectedAnswers.value[currentQuestion.value.id] = answer === 'true'
  } else {
    selectedAnswers.value[currentQuestion.value.id] = answer
  }
}

function submitAnswer() {
  showResult.value = true
  answeredCount.value++
  
  const correct = checkAnswer()
  if (correct) correctCount.value++
}

function checkAnswer(): boolean {
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
  if (currentIndex.value < filteredQuestions.value.length - 1) {
    currentIndex.value++
    showResult.value = false
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    showResult.value = false
  }
}

function restart() {
  currentIndex.value = 0
  selectedAnswers.value = {}
  showResult.value = false
  answeredCount.value = 0
  correctCount.value = 0
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
  if (!showResult.value) {
    if (currentQuestion.value.type === 'multiple') {
      const selected = (selectedAnswers.value[currentQuestion.value.id] as string[]) || []
      return selected.includes(option.label)
        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
        : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
    } else if (currentQuestion.value.type === 'judge') {
      const selected = selectedAnswers.value[currentQuestion.value.id] as boolean
      const isTrue = option.label === 'true'
      return selected === isTrue
        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
        : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
    }
    return selectedAnswers.value[currentQuestion.value.id] === option.label
      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
      : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
  }
  
  const isCorrect = currentQuestion.value.type === 'multiple'
    ? (currentQuestion.value.answer as string[]).includes(option.label)
    : currentQuestion.value.type === 'judge'
      ? (option.label === 'true') === currentQuestion.value.answer
      : option.label === currentQuestion.value.answer
  
  const isSelected = currentQuestion.value.type === 'multiple'
    ? ((selectedAnswers.value[currentQuestion.value.id] as string[]) || []).includes(option.label)
    : currentQuestion.value.type === 'judge'
      ? ((selectedAnswers.value[currentQuestion.value.id] as boolean) === (option.label === 'true'))
      : selectedAnswers.value[currentQuestion.value.id] === option.label
  
  if (isCorrect) return 'border-green-500 bg-green-50 text-green-700'
  if (isSelected && !isCorrect) return 'border-red-500 bg-red-50 text-red-700'
  return 'border-gray-200 opacity-50'
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">题目总数</div>
        <div class="text-3xl font-bold mt-2">{{ filteredQuestions.length }}题</div>
      </div>
      <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">已答题数</div>
        <div class="text-3xl font-bold mt-2">{{ answeredCount }}题</div>
      </div>
      <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">正确率</div>
        <div class="text-3xl font-bold mt-2">{{ answeredCount > 0 ? Math.round((correctCount / answeredCount) * 100) : 0 }}%</div>
      </div>
      <div class="bg-gradient-to-br from-pink-500 to-rose-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">当前进度</div>
        <div class="text-3xl font-bold mt-2">{{ currentIndex + 1 }}/{{ filteredQuestions.length }}</div>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-lg p-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div class="flex items-center gap-4">
          <select v-model="selectedSubject" class="input-field w-48">
            <option value="all">全部科目</option>
            <option v-for="subject in subjects" :key="subject" :value="subject">{{ subject }}</option>
          </select>
          <select v-model="selectedChapter" class="input-field w-48">
            <option value="all">全部章节</option>
            <option v-for="chapter in chapters" :key="chapter" :value="chapter">{{ chapter }}</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="practiceMode = 'sequence'"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              practiceMode === 'sequence'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            顺序练习
          </button>
          <button
            @click="practiceMode = 'random'"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              practiceMode === 'random'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            随机练习
          </button>
          <button @click="restart" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg font-medium hover:bg-gray-200 transition-all">
            🔄 重新开始
          </button>
        </div>
      </div>

      <div class="h-2 bg-gray-200 rounded-full overflow-hidden mb-6">
        <div
          class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
          :style="{ width: progress + '%' }"
        ></div>
      </div>

      <div v-if="currentQuestion" class="space-y-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="badge bg-indigo-100 text-indigo-700">{{ currentQuestion.subject }}</span>
            <span class="badge bg-gray-100 text-gray-700">{{ currentQuestion.chapter }}</span>
            <span :class="['badge', getQuestionTypeClass(currentQuestion.type)]">
              {{ getQuestionTypeLabel(currentQuestion.type) }}
            </span>
          </div>
          <span class="text-gray-500">第 {{ currentIndex + 1 }} 题</span>
        </div>

        <div class="bg-gray-50 rounded-xl p-6">
          <div class="text-lg font-medium text-gray-800">{{ currentQuestion.question }}</div>
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
            <span class="font-medium mr-3">{{ option.label }}.</span>
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
            <div class="text-2xl mb-2">✅</div>
            <div class="font-medium">正确</div>
          </button>
          <button
            @click="selectAnswer('false')"
            :disabled="showResult"
            :class="[
              'p-6 rounded-xl border-2 transition-all text-center',
              getOptionClass({ label: 'false' })
            ]"
          >
            <div class="text-2xl mb-2">❌</div>
            <div class="font-medium">错误</div>
          </button>
        </div>

        <div v-if="showResult" class="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <div class="flex items-center gap-2 mb-3">
            <span class="text-xl">💡</span>
            <span class="font-medium text-amber-800">答案解析</span>
          </div>
          <p class="text-amber-700">{{ currentQuestion.analysis }}</p>
        </div>

        <div class="flex items-center justify-between pt-4 border-t border-gray-100">
          <button
            @click="prevQuestion"
            :disabled="currentIndex === 0"
            class="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← 上一题
          </button>
          
          <div v-if="!showResult" class="flex-1 flex justify-center">
            <button
              @click="submitAnswer"
              class="px-8 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all shadow-lg"
            >
              提交答案
            </button>
          </div>
          <div v-else class="flex-1 flex justify-center">
            <button
              v-if="currentIndex < filteredQuestions.length - 1"
              @click="nextQuestion"
              class="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg"
            >
              下一题 →
            </button>
            <button
              v-else
              @click="restart"
              class="px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium rounded-xl hover:from-amber-600 hover:to-orange-700 transition-all shadow-lg"
            >
              🔄 完成练习，重新开始
            </button>
          </div>

          <button
            @click="nextQuestion"
            :disabled="currentIndex === filteredQuestions.length - 1 || !showResult"
            class="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一题 →
          </button>
        </div>
      </div>

      <div v-else class="text-center py-16">
        <div class="text-6xl mb-4">📭</div>
        <div class="text-gray-500">暂无符合条件的题目</div>
      </div>
    </div>
  </div>
</template>
