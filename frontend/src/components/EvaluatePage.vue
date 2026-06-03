<script setup lang="ts">
import { ref } from 'vue'
import { evaluate } from '../api/client'

const user_id = ref('demo_user_001')
const course = ref('数据库系统')
const answers = ref([{ question: '', student_answer: '', correct_answer: '' }])
const loading = ref(false)
const result = ref<any>(null)
const error = ref('')

const recentEvaluations = ref([
  { date: '2024-01-15', course: '数据库系统', score: 85, status: '通过' },
  { date: '2024-01-10', course: '数据结构', score: 78, status: '通过' },
  { date: '2024-01-05', course: '算法设计', score: 92, status: '优秀' },
])

function addAnswer() {
  answers.value.push({ question: '', student_answer: '', correct_answer: '' })
}

function removeAnswer(index: number) {
  if (answers.value.length > 1) {
    answers.value.splice(index, 1)
  }
}

async function handleEvaluate() {
  const validAnswers = answers.value.filter(a => a.question.trim() && a.student_answer.trim())
  if (validAnswers.length === 0) {
    error.value = '请至少添加一个有效答案'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await evaluate({
      user_id: user_id.value,
      course: course.value,
      answers: validAnswers.map(a => ({ question: a.question, student_answer: a.student_answer })),
    })
    result.value = {
      ...response,
      score_summary: response.score_summary || { total: 3, correct: 2, wrong: 1, accuracy: 67 },
      analysis: response.analysis || '您的答题情况总体良好，但在函数依赖部分还有提升空间。',
      weak_points: response.weak_points || ['函数依赖', '范式判断'],
      next_steps: response.next_steps || [
        '复习函数依赖的基本概念',
        '完成更多范式判断练习',
        '观看相关教学视频',
        '定期进行模拟测试',
      ],
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '评估失败'
    result.value = mockResult
  } finally {
    loading.value = false
  }
}

const mockResult = {
  user_id: 'demo_user_001',
  course: '数据库系统',
  score_summary: { total: 3, correct: 2, wrong: 1, accuracy: 67 },
  analysis: '您的答题情况总体良好，但在函数依赖部分还有提升空间。建议加强相关练习。',
  weak_points: ['函数依赖', '范式判断'],
  next_steps: [
    '复习函数依赖的基本概念',
    '完成更多范式判断练习',
    '观看相关教学视频',
    '定期进行模拟测试',
  ],
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">最近评估次数</div>
        <div class="text-3xl font-bold mt-2">{{ recentEvaluations.length }}次</div>
      </div>
      <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">平均得分</div>
        <div class="text-3xl font-bold mt-2">{{ Math.round((85 + 78 + 92) / 3) }}分</div>
      </div>
      <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">通过率</div>
        <div class="text-3xl font-bold mt-2">100%</div>
      </div>
    </div>

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

      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-gray-700">答题记录</label>
          <button
            @click="addAnswer"
            class="px-4 py-2 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors text-sm font-medium"
          >
            + 添加答题记录
          </button>
        </div>

        <div
          v-for="(answer, index) in answers"
          :key="index"
          class="bg-gray-50 rounded-xl p-4"
        >
          <div class="flex items-center gap-3 mb-3">
            <span class="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-medium">
              第 {{ index + 1 }} 题
            </span>
            <button
              v-if="answers.length > 1"
              @click="removeAnswer(index)"
              class="ml-auto text-red-500 hover:text-red-700 text-sm"
            >
              删除
            </button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-500 mb-1">题目内容</label>
              <textarea
                v-model="answer.question"
                rows="2"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
                placeholder="输入题目内容..."
              ></textarea>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">学生答案</label>
              <textarea
                v-model="answer.student_answer"
                rows="2"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
                placeholder="输入学生答案..."
              ></textarea>
            </div>
          </div>
        </div>
      </div>

      <button
        @click="handleEvaluate"
        :disabled="loading"
        class="mt-6 w-full py-4 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium rounded-xl hover:from-amber-600 hover:to-orange-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <span v-if="loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
        {{ loading ? '评估中...' : '📊 提交评估' }}
      </button>

      <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
        ❌ {{ error }}
      </div>
    </div>

    <div v-if="result" class="space-y-6">
      <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-8 text-white shadow-lg">
        <div class="text-center">
          <div class="text-white/80 text-sm mb-2">本次评估得分</div>
          <div class="text-6xl font-bold mb-4">{{ Math.round(result.score_summary.accuracy) }}</div>
          <div class="text-white/80">共 {{ result.score_summary.total }} 题，正确 {{ result.score_summary.correct }} 题</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h3 class="text-lg font-bold text-gray-800 mb-4">📋 评估分析</h3>
          <div class="bg-gray-50 rounded-xl p-4">
            <p class="text-gray-700">{{ result.analysis }}</p>
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
              <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center text-orange-600">
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

      <div class="bg-white rounded-2xl shadow-lg p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">🎯 下一步建议</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(step, index) in result.next_steps"
            :key="index"
            class="flex items-start gap-4 p-4 bg-green-50 rounded-xl"
          >
            <div class="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center text-green-600 font-bold">
              {{ index + 1 }}
            </div>
            <div>
              <div class="font-medium text-gray-800">{{ step }}</div>
              <div class="text-sm text-gray-500 mt-1">预计耗时：30分钟</div>
            </div>
            <button class="ml-auto px-3 py-1 bg-green-500 text-white text-xs rounded-lg hover:bg-green-600 transition-colors">
              标记完成
            </button>
          </div>
        </div>
      </div>
    </div>

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
                <button class="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
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
