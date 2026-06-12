<script setup lang="ts">
import { ref, computed } from 'vue'
import { analyze } from '../api/client'

const user_id = ref('demo_user_001')
const course = ref('数据库系统')
const message = ref('')
const loading = ref(false)
const analysis = ref<any>(null)
const error = ref('')

const analysisTabs = [
  { key: 'overview', label: '概览', icon: '📊' },
  { key: 'weakPoints', label: '薄弱环节', icon: '💡' },
  { key: 'suggestions', label: '学习建议', icon: '🎯' },
]
const activeTab = ref('overview')

async function handleAnalyze() {
  if (!message.value.trim()) {
    error.value = '请输入学习需求'
    return
  }

  loading.value = true
  error.value = ''
  analysis.value = null

  try {
    const response = await analyze({
      user_id: user_id.value,
      course: course.value,
      message: message.value
    })
    analysis.value = {
      ...response.profile,
      statistics: {
        totalStudyTime: '86小时',
        averageScore: 85,
        completedCourses: 12,
        studyDays: 45,
      },
      weeklyData: [6, 8, 4, 10, 7, 9, 5],
      weakPoints: response.profile?.weak_points || [],
      suggestions: [
        '建议加强函数依赖和范式判断的练习',
        '每天至少复习30分钟数据库知识',
        '完成课后习题并总结错题',
        '观看相关教学视频加深理解',
      ]
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析失败'
    analysis.value = mockAnalysisData
  } finally {
    loading.value = false
  }
}

const mockAnalysisData = {
  major: '计算机科学与技术',
  course: '数据库系统',
  grade_level: '大三',
  learning_goal: '准备期末考试',
  knowledge_level: '中等',
  learning_style: '视觉型',
  weak_points: ['函数依赖', '候选码', '范式判断'],
  resource_preference: ['视频教程', '练习题', '思维导图'],
  statistics: {
    totalStudyTime: '86小时',
    averageScore: 85,
    completedCourses: 12,
    studyDays: 45,
  },
  weeklyData: [6, 8, 4, 10, 7, 9, 5],
  suggestions: [
    '建议加强函数依赖和范式判断的练习',
    '每天至少复习30分钟数据库知识',
    '完成课后习题并总结错题',
    '观看相关教学视频加深理解',
  ]
}

const maxWeeklyHours = computed(() => {
  return Math.max(...(analysis.value?.weeklyData || [0]))
})
</script>

<template>
  <div class="space-y-6">
    <div class="bg-white rounded-2xl shadow-lg p-6">
      <h2 class="text-lg font-bold text-gray-800 mb-4">🔍 学习分析设置</h2>
      <form @submit.prevent="handleAnalyze" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">用户ID</label>
          <input
            v-model="user_id"
            type="text"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            placeholder="输入用户ID"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">课程</label>
          <select
            v-model="course"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          >
            <option value="数据库系统">数据库系统</option>
            <option value="数据结构">数据结构</option>
            <option value="算法设计">算法设计</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">需求描述</label>
          <input
            v-model="message"
            type="text"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            placeholder="描述您的学习需求..."
          />
        </div>
        <div class="md:col-span-3">
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <span v-if="loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            {{ loading ? '分析中...' : '开始分析' }}
          </button>
        </div>
      </form>
      <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
        ❌ {{ error }}
      </div>
    </div>

    <div v-if="analysis" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
          <div class="text-white/80 text-sm">总学习时长</div>
          <div class="text-3xl font-bold mt-2">{{ analysis.statistics.totalStudyTime }}</div>
          <div class="flex items-center gap-1 mt-2 text-white/80 text-sm">
            <span>📈</span>
            <span>较上周 +12%</span>
          </div>
        </div>
        <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg">
          <div class="text-white/80 text-sm">平均得分</div>
          <div class="text-3xl font-bold mt-2">{{ analysis.statistics.averageScore }}分</div>
          <div class="flex items-center gap-1 mt-2 text-white/80 text-sm">
            <span>🎯</span>
            <span>班级排名前20%</span>
          </div>
        </div>
        <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
          <div class="text-white/80 text-sm">已完成课程</div>
          <div class="text-3xl font-bold mt-2">{{ analysis.statistics.completedCourses }}门</div>
          <div class="flex items-center gap-1 mt-2 text-white/80 text-sm">
            <span>✅</span>
            <span>进度75%</span>
          </div>
        </div>
        <div class="bg-gradient-to-br from-pink-500 to-rose-600 rounded-2xl p-6 text-white shadow-lg">
          <div class="text-white/80 text-sm">连续学习</div>
          <div class="text-3xl font-bold mt-2">{{ analysis.statistics.studyDays }}天</div>
          <div class="flex items-center gap-1 mt-2 text-white/80 text-sm">
            <span>🔥</span>
            <span>保持良好习惯</span>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div class="grid grid-cols-3 bg-gray-50">
          <button
            v-for="tab in analysisTabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'py-4 font-medium transition-colors flex items-center justify-center gap-2',
              activeTab === tab.key ? 'text-indigo-600 border-b-2 border-indigo-600 bg-white' : 'text-gray-600 hover:text-gray-800'
            ]"
          >
            <span>{{ tab.icon }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </div>

        <div class="p-6">
          <div v-if="activeTab === 'overview'">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div class="bg-gray-50 rounded-xl p-6">
                <h3 class="font-medium text-gray-800 mb-4">📊 学习档案</h3>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <div class="text-sm text-gray-500">专业</div>
                    <div class="font-medium">{{ analysis.major }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">课程</div>
                    <div class="font-medium">{{ analysis.course }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">年级</div>
                    <div class="font-medium">{{ analysis.grade_level }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">学习目标</div>
                    <div class="font-medium">{{ analysis.learning_goal }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">知识水平</div>
                    <div class="font-medium">{{ analysis.knowledge_level }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">学习风格</div>
                    <div class="font-medium">{{ analysis.learning_style }}</div>
                  </div>
                </div>
              </div>

              <div class="bg-gray-50 rounded-xl p-6">
                <h3 class="font-medium text-gray-800 mb-4">📅 本周学习时长</h3>
                <div class="flex items-end justify-between h-40 gap-2">
                  <div
                    v-for="(hours, index) in analysis.weeklyData"
                    :key="index"
                    class="flex-1 flex flex-col items-center gap-2"
                  >
                    <div 
                      class="w-full bg-gradient-to-t from-indigo-500 to-purple-500 rounded-t-lg transition-all duration-500"
                      :style="{ height: (hours / maxWeeklyHours * 120) + 'px' }"
                    ></div>
                    <span class="text-xs text-gray-500">{{ ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][index] }}</span>
                    <span class="text-xs font-medium text-gray-700">{{ hours }}h</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'weakPoints'">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div
                v-for="(point, index) in analysis.weakPoints"
                :key="index"
                class="bg-orange-50 border border-orange-200 rounded-xl p-6"
              >
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center text-xl">
                    💡
                  </div>
                  <div>
                    <div class="font-medium text-gray-800">薄弱环节 {{ index + 1 }}</div>
                    <div class="text-sm text-gray-500">需要重点关注</div>
                  </div>
                </div>
                <div class="text-lg font-bold text-orange-600">{{ point }}</div>
                <div class="mt-3 text-sm text-gray-600">
                  建议：加强练习，观看相关教学视频
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'suggestions'">
            <div class="space-y-4">
              <div
                v-for="(suggestion, index) in analysis.suggestions"
                :key="index"
                class="flex items-start gap-4 p-4 bg-green-50 rounded-xl"
              >
                <div class="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center text-green-600 font-bold">
                  {{ Number(index) + 1 }}
                </div>
                <div>
                  <div class="font-medium text-gray-800">{{ suggestion }}</div>
                  <div class="text-sm text-gray-500 mt-1">预计提升效果：中等</div>
                </div>
                <button class="ml-auto px-4 py-2 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600 transition-colors">
                  标记已完成
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
