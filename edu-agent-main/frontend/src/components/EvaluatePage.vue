<script setup lang="ts">
import { ref, computed } from 'vue'
import { smartEvaluate, startQuiz, answerQuiz, finishQuiz } from '../api/client'

const user_id = ref('demo_user_001')
const course = ref('数据库系统')
const activeMode = ref<'smart' | 'quiz'>('smart')
const loading = ref(false)
const result = ref<any>(null)
const error = ref('')
const completedSteps = ref<Set<number>>(new Set())

const quizState = ref({
  questions: [] as any[],
  currentIndex: 0,
  answers: {} as Record<string, string>,
  isFinished: false,
})

const recentEvaluations = ref([
  { date: '2024-01-15', course: '数据库系统', score: 85, status: '通过', duration: '25分钟', questions: 5 },
  { date: '2024-01-10', course: '数据结构', score: 78, status: '通过', duration: '30分钟', questions: 6 },
  { date: '2024-01-05', course: '算法设计', score: 92, status: '优秀', duration: '20分钟', questions: 4 },
])

const averageScore = computed(() => {
  if (recentEvaluations.value.length === 0) return 0
  return Math.round(recentEvaluations.value.reduce((sum, e) => sum + e.score, 0) / recentEvaluations.value.length)
})

const passRate = computed(() => {
  const passed = recentEvaluations.value.filter(e => e.score >= 60).length
  return Math.round((passed / recentEvaluations.value.length) * 100)
})

function getScoreLevel(score: number) {
  if (score >= 90) return { text: '优秀', class: 'bg-green-100 text-green-700', icon: '🏆' }
  if (score >= 80) return { text: '良好', class: 'bg-blue-100 text-blue-700', icon: '👍' }
  if (score >= 60) return { text: '通过', class: 'bg-amber-100 text-amber-700', icon: '✅' }
  return { text: '需加强', class: 'bg-red-100 text-red-700', icon: '💪' }
}

function toggleStepComplete(index: number) {
  if (completedSteps.value.has(index)) {
    completedSteps.value.delete(index)
  } else {
    completedSteps.value.add(index)
  }
}

async function handleSmartEvaluate() {
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await smartEvaluate({
      user_id: user_id.value,
      course: course.value,
    })
    result.value = response
    completedSteps.value.clear()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '智能评估失败'
    result.value = mockSmartResult
  } finally {
    loading.value = false
  }
}

async function handleStartQuiz() {
  loading.value = true
  error.value = ''
  quizState.value = { questions: [], currentIndex: 0, answers: {}, isFinished: false }
  result.value = null

  try {
    const response = await startQuiz({
      user_id: user_id.value,
      course: course.value,
    })
    quizState.value.questions = [response.question]
    quizState.value.currentIndex = response.current_index
  } catch (err) {
    error.value = err instanceof Error ? err.message : '启动测试失败'
  } finally {
    loading.value = false
  }
}

async function handleQuizAnswer() {
  const currentQuestion = quizState.value.questions[quizState.value.currentIndex]
  if (!currentQuestion) return

  loading.value = true
  error.value = ''

  try {
    const response = await answerQuiz({
      user_id: user_id.value,
      course: course.value,
      question_id: currentQuestion.question_id,
      answer: (quizState.value.answers[currentQuestion.question_id] || '').trim(),
    })

    quizState.value.currentIndex = response.current_index
    if (response.question) {
      quizState.value.questions.push(response.question)
    } else {
      quizState.value.isFinished = true
      await handleFinishQuiz()
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '提交答案失败'
  } finally {
    loading.value = false
  }
}

async function handleFinishQuiz() {
  loading.value = true
  error.value = ''

  try {
    const response = await finishQuiz({
      user_id: user_id.value,
      course: course.value,
    })
    result.value = response
    completedSteps.value.clear()

    const accuracy = Math.round(response.score_summary.accuracy)
    const level = getScoreLevel(accuracy)
    recentEvaluations.value.unshift({
      date: new Date().toISOString().split('T')[0],
      course: course.value,
      score: accuracy,
      status: level.text,
      duration: '约15分钟',
      questions: response.score_summary.total,
    })
    if (recentEvaluations.value.length > 10) {
      recentEvaluations.value.pop()
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '完成测试失败'
  } finally {
    loading.value = false
  }
}

function viewDetail(record: any) {
  alert(`查看评估详情：${record.course} - ${record.date}`)
}

const mockSmartResult = {
  user_id: 'demo_user_001',
  course: '数据库系统',
  profile_summary: {
    knowledge_level: '中级',
    learning_style: '视觉型',
    learning_goal: '考试准备',
  },
  score_summary: { total: 4, correct: 75, wrong: 25, accuracy: 75 },
  weak_points: ['函数依赖', '范式判断'],
  completed_topics: ['关系模型', 'SQL基础'],
  in_progress_topics: ['事务', '索引'],
  analysis: '基于您的学习画像分析：\n- 您的知识水平目前处于中级阶段\n- 学习风格为视觉型，建议多使用图表和思维导图\n- 已掌握的知识点：关系模型、SQL基础\n- 需要加强的知识点：函数依赖、范式判断\n\n综合评估：您的整体表现良好，建议重点复习薄弱环节。',
  next_steps: [
    { title: '重点复习：函数依赖、范式判断', duration: '45分钟', type: 'review' },
    { title: '完成相关章节的练习题', duration: '30分钟', type: 'practice' },
    { title: '观看教学视频加深理解', duration: '20分钟', type: 'video' },
    { title: '进行一次模拟测试检验学习效果', duration: '60分钟', type: 'test' },
  ],
}
</script>

<template>
  <div class="space-y-6">
    <!-- 顶部统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">最近评估次数</div>
        <div class="text-3xl font-bold mt-2">{{ recentEvaluations.length }}次</div>
      </div>
      <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">平均得分</div>
        <div class="text-3xl font-bold mt-2">{{ averageScore }}分</div>
      </div>
      <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">通过率</div>
        <div class="text-3xl font-bold mt-2">{{ passRate }}%</div>
      </div>
    </div>

    <!-- 评估表单区域 -->
    <div class="bg-white rounded-2xl shadow-lg p-6">
      <h2 class="text-lg font-bold text-gray-800 mb-6">📝 学习评估</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">用户ID</label>
          <input
            v-model="user_id"
            type="text"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            placeholder="输入用户ID"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">课程</label>
          <select
            v-model="course"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          >
            <option value="数据库系统">数据库系统</option>
            <option value="数据结构">数据结构</option>
            <option value="算法设计">算法设计</option>
          </select>
        </div>
      </div>

      <!-- 评估模式选择 -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-3">选择评估方式</label>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            @click="activeMode = 'smart'"
            :class="[
              'py-3 px-4 rounded-xl font-medium transition-all text-sm',
              activeMode === 'smart'
                ? 'bg-amber-500 text-white shadow-md'
                : 'bg-gray-100 text-gray-700 hover:bg-amber-100'
            ]"
          >
            🤖 智能评估
          </button>
          <button
            @click="activeMode = 'quiz'"
            :class="[
              'py-3 px-4 rounded-xl font-medium transition-all text-sm',
              activeMode === 'quiz'
                ? 'bg-blue-500 text-white shadow-md'
                : 'bg-gray-100 text-gray-700 hover:bg-blue-100'
            ]"
          >
            ✨ 智能小测
          </button>
        </div>
      </div>

      <!-- 智能评估模式 -->
      <div v-if="activeMode === 'smart'" class="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 mb-6">
        <p class="text-sm text-gray-600">
          💡 基于您的学习画像和历史记录，自动分析评估学习效果
        </p>
        <button
          @click="handleSmartEvaluate"
          :disabled="loading"
          class="mt-4 w-full py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium rounded-xl hover:from-amber-600 hover:to-orange-700 transition-all disabled:opacity-50"
        >
          <span v-if="loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block mr-2"></span>
          {{ loading ? '分析中...' : '🚀 开始智能评估' }}
        </button>
      </div>

      <!-- 智能小测模式 -->
      <div v-if="activeMode === 'quiz'" class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 mb-6">
        <p class="text-sm text-gray-600">
          🎮 系统根据您的薄弱点自动出题，进行针对性测试
        </p>
        <button
          v-if="!quizState.isFinished && quizState.questions.length === 0"
          @click="handleStartQuiz"
          :disabled="loading"
          class="mt-4 w-full py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all disabled:opacity-50"
        >
          <span v-if="loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block mr-2"></span>
          {{ loading ? '加载中...' : '🎯 开始智能小测' }}
        </button>
      </div>

      <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
        ❌ {{ error }}
      </div>
    </div>

    <!-- 智能小测题目 -->
    <div v-if="quizState.questions.length > 0 && !quizState.isFinished" class="bg-white rounded-2xl shadow-lg p-6">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-bold text-gray-800">
          🎯 智能小测 - 第 {{ quizState.currentIndex + 1 }} / {{ quizState.questions.length }} 题
        </h3>
        <div class="flex gap-2">
          <div
            v-for="(_, index) in quizState.questions"
            :key="index"
            :class="[
              'w-3 h-3 rounded-full transition-colors',
              index === quizState.currentIndex ? 'bg-amber-500' : 'bg-gray-200'
            ]"
          ></div>
        </div>
      </div>

      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4">
          <span class="px-2 py-1 bg-blue-100 text-blue-600 rounded-lg text-xs font-medium">
            {{ quizState.questions[quizState.currentIndex]?.topic }}
          </span>
        </div>

        <div class="text-lg font-medium text-gray-800 mb-6">
          {{ quizState.questions[quizState.currentIndex]?.question }}
        </div>

        <div v-if="quizState.questions[quizState.currentIndex]?.options" class="space-y-3">
          <label
            v-for="(option, idx) in quizState.questions[quizState.currentIndex]?.options"
            :key="idx"
            :class="[
              'flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all',
              quizState.answers[quizState.questions[quizState.currentIndex]?.question_id] === String.fromCharCode(65 + idx)
                ? 'bg-blue-100 border-2 border-blue-500'
                : 'bg-white border-2 border-gray-200 hover:border-blue-300'
            ]"
          >
            <div :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center font-medium',
              quizState.answers[quizState.questions[quizState.currentIndex]?.question_id] === String.fromCharCode(65 + idx)
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600'
            ]">
              {{ String.fromCharCode(65 + idx) }}
            </div>
            <span class="text-gray-800">{{ option }}</span>
            <input
              type="radio"
              :value="String.fromCharCode(65 + idx)"
              v-model="quizState.answers[quizState.questions[quizState.currentIndex]?.question_id]"
              class="hidden"
            />
          </label>
        </div>

        <div v-else class="mt-3">
          <input
            v-model="quizState.answers[quizState.questions[quizState.currentIndex]?.question_id]"
            type="text"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="请输入答案..."
          />
        </div>
      </div>

      <button
        @click="handleQuizAnswer"
        :disabled="loading || !quizState.answers[quizState.questions[quizState.currentIndex]?.question_id]"
        class="mt-6 w-full py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all disabled:opacity-50"
      >
        <span v-if="loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block mr-2"></span>
        {{ loading ? '提交中...' : '➡️ 下一题' }}
      </button>
    </div>

    <!-- 评估结果 -->
    <div v-if="result" class="space-y-6">
      <!-- 得分展示 -->
      <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-8 text-white shadow-lg">
        <div class="text-center">
          <div class="text-white/80 text-sm mb-2">{{ activeMode === 'smart' ? '智能评估结果' : '测试评估结果' }}</div>
          <div class="text-6xl font-bold mb-4">{{ Math.round(result.score_summary.accuracy) }}</div>
          <div class="text-white/80">共 {{ result.score_summary.total }} 题，正确 {{ result.score_summary.correct }} 题</div>
        </div>
        <div class="mt-6 bg-white/10 rounded-xl p-4">
          <div class="flex items-center justify-between text-sm mb-2">
            <span>正确率</span>
            <span>{{ Math.round(result.score_summary.accuracy) }}%</span>
          </div>
          <div class="h-3 bg-white/20 rounded-full overflow-hidden">
            <div
              class="h-full bg-white rounded-full transition-all duration-1000"
              :style="{ width: result.score_summary.accuracy + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- 评估分析和薄弱环节 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h3 class="text-lg font-bold text-gray-800 mb-4">📋 评估分析</h3>
          <div class="bg-gray-50 rounded-xl p-4">
            <p class="text-gray-700 whitespace-pre-line">{{ result.analysis }}</p>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h3 class="text-lg font-bold text-gray-800 mb-4">💡 薄弱环节</h3>
          <div class="space-y-3">
            <div
              v-for="(point, index) in result.weak_points"
              :key="index"
              class="flex items-center gap-3 p-3 bg-orange-50 rounded-xl"
            >
              <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center text-orange-600 font-bold">
                {{ index + 1 }}
              </div>
              <div>
                <div class="font-medium text-gray-800">{{ point }}</div>
                <div class="text-xs text-gray-500">需要加强练习</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 学生画像摘要 -->
      <div v-if="result.profile_summary" class="bg-white rounded-2xl shadow-lg p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">👤 学习画像摘要</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-purple-50 rounded-xl p-4 text-center">
            <div class="text-sm text-gray-500">知识水平</div>
            <div class="text-xl font-bold text-purple-700 mt-1">{{ result.profile_summary.knowledge_level }}</div>
          </div>
          <div class="bg-blue-50 rounded-xl p-4 text-center">
            <div class="text-sm text-gray-500">学习风格</div>
            <div class="text-xl font-bold text-blue-700 mt-1">{{ result.profile_summary.learning_style }}</div>
          </div>
          <div class="bg-green-50 rounded-xl p-4 text-center">
            <div class="text-sm text-gray-500">学习目标</div>
            <div class="text-xl font-bold text-green-700 mt-1">{{ result.profile_summary.learning_goal }}</div>
          </div>
        </div>
      </div>

      <!-- 已掌握知识点 -->
      <div v-if="result.completed_topics && result.completed_topics.length > 0" class="bg-white rounded-2xl shadow-lg p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">✅ 已掌握知识点</h3>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="topic in result.completed_topics"
            :key="topic"
            class="px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm font-medium"
          >
            ✓ {{ topic }}
          </span>
        </div>
      </div>

      <!-- 下一步建议 -->
      <div class="bg-white rounded-2xl shadow-lg p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">🎯 下一步建议</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(step, index) in (result.next_steps || [])"
            :key="index"
            class="flex items-start gap-4 p-4 rounded-xl transition-all"
            :class="completedSteps.has(index) ? 'bg-green-50' : 'bg-green-50 hover:bg-green-100'"
          >
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center text-lg cursor-pointer transition-all"
              :class="completedSteps.has(index) ? 'bg-green-500 text-white' : 'bg-green-100 text-green-600 hover:bg-green-200'"
              @click="toggleStepComplete(index)"
            >
              {{ completedSteps.has(index) ? '✓' :
                 (typeof step === 'string' ? '📖' :
                 step.type === 'review' ? '📖' :
                 step.type === 'practice' ? '✏️' :
                 step.type === 'video' ? '🎬' : '🧪') }}
            </div>
            <div class="flex-1">
              <div :class="['font-medium', completedSteps.has(index) ? 'text-green-700 line-through' : 'text-gray-800']">
                {{ typeof step === 'string' ? step : step.title }}
              </div>
              <div class="text-sm text-gray-500 mt-1">
                ⏱️ {{ typeof step === 'string' ? '30分钟' : step.duration }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 答题详情 -->
      <div v-if="result.detailed_results && result.detailed_results.length > 0" class="bg-white rounded-2xl shadow-lg p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">📝 答题详情</h3>
        <div class="space-y-4">
          <div
            v-for="(detail, index) in result.detailed_results"
            :key="index"
            :class="[
              'rounded-xl border-2 p-4',
              detail.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
            ]"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="px-3 py-1 bg-white rounded-lg text-sm font-medium">
                  第 {{ index + 1 }} 题
                </span>
                <span :class="[
                  'px-3 py-1 rounded-lg text-sm font-medium',
                  detail.is_correct ? 'bg-green-200 text-green-700' : 'bg-red-200 text-red-700'
                ]">
                  {{ detail.is_correct ? '✓ 正确' : '✗ 错误' }}
                </span>
              </div>
            </div>
            <div class="text-gray-800 mb-3">{{ detail.question }}</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <div class="text-xs text-gray-500 mb-1">您的答案</div>
                <div :class="[
                  'px-3 py-2 rounded-lg text-sm',
                  detail.is_correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                ]">
                  {{ detail.user_answer || '未作答' }}
                </div>
              </div>
              <div>
                <div class="text-xs text-gray-500 mb-1">正确答案</div>
                <div class="px-3 py-2 bg-gray-100 rounded-lg text-sm text-gray-700">
                  {{ detail.correct_answer }}
                </div>
              </div>
            </div>
            <div class="mt-3 p-3 bg-white/50 rounded-lg">
              <div class="text-xs text-gray-500 mb-1">解析</div>
              <div class="text-sm text-gray-600">{{ detail.explanation }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史评估记录 -->
    <div class="bg-white rounded-2xl shadow-lg p-6">
      <h3 class="text-lg font-bold text-gray-800 mb-4">📜 历史评估记录</h3>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200">
              <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">日期</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">课程</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">得分</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">状态</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(record, index) in recentEvaluations"
              :key="index"
              class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
            >
              <td class="py-4 px-4 text-sm text-gray-800">{{ record.date }}</td>
              <td class="py-4 px-4 text-sm text-gray-800">{{ record.course }}</td>
              <td class="py-4 px-4">
                <span :class="[
                  'px-3 py-1 rounded-full text-sm font-medium',
                  record.score >= 90 ? 'bg-green-100 text-green-700' :
                  record.score >= 70 ? 'bg-blue-100 text-blue-700' :
                  'bg-red-100 text-red-700'
                ]">
                  {{ record.score }}分
                </span>
              </td>
              <td class="py-4 px-4">
                <span :class="[
                  'px-3 py-1 rounded-full text-sm font-medium',
                  record.status === '优秀' ? 'bg-green-100 text-green-700' :
                  'bg-blue-100 text-blue-700'
                ]">
                  {{ record.status }}
                </span>
              </td>
              <td class="py-4 px-4">
                <button
                  @click="viewDetail(record)"
                  class="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                >
                  查看详情 →
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
