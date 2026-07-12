<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { analyze } from '../api/client'
import type { Course } from '../types'

const props = defineProps<{
  course: Course | null
}>()

const emit = defineEmits<{
  navigate: [page: 'detail']
}>()

const user_id = ref('demo_user_001')
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
  if (!props.course) return

  loading.value = true
  error.value = ''
  analysis.value = null

  try {
    const response = await analyze({
      user_id: user_id.value,
      course: props.course.name,
      message: '分析我的学习情况'
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
  course: props.course?.name || '数据库系统',
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

onMounted(() => {
  handleAnalyze()
})
</script>

<template>
  <div class="space-y-6">
    <section class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div class="flex items-center justify-between mb-6">
        <div>
          <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">LEARNING ANALYSIS</div>
          <h1 class="text-2xl font-bold text-gray-900">学习分析报告</h1>
          <p class="text-gray-500 mt-2">当前课程：{{ course?.name || '未知课程' }}</p>
        </div>
        <button
          @click="emit('navigate', 'detail')"
          class="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium transition-all"
        >
          返回课程详情
        </button>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-12">
        <div class="w-12 h-12 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin mb-4"></div>
        <span class="text-gray-500">正在分析学习数据...</span>
      </div>

      <div v-if="error" class="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm">
        {{ error }}
      </div>
    </section>

    <div v-if="analysis && !loading" class="space-y-6">
      <section class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="text-sm text-gray-500 mb-2">总学习时长</div>
            <div class="text-2xl font-bold text-gray-900">{{ analysis.statistics.totalStudyTime }}</div>
            <div class="text-xs text-green-600 mt-2">较上周 +12%</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="text-sm text-gray-500 mb-2">平均得分</div>
            <div class="text-2xl font-bold text-gray-900">{{ analysis.statistics.averageScore }}分</div>
            <div class="text-xs text-gray-500 mt-2">班级排名前20%</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="text-sm text-gray-500 mb-2">已完成课程</div>
            <div class="text-2xl font-bold text-gray-900">{{ analysis.statistics.completedCourses }}门</div>
            <div class="text-xs text-gray-500 mt-2">进度75%</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="text-sm text-gray-500 mb-2">连续学习</div>
            <div class="text-2xl font-bold text-gray-900">{{ analysis.statistics.studyDays }}天</div>
            <div class="text-xs text-gray-500 mt-2">保持良好习惯</div>
          </div>
        </div>
      </section>

      <section class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="grid grid-cols-3 bg-gray-50">
          <button
            v-for="tab in analysisTabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'py-4 font-medium transition-colors flex items-center justify-center gap-2',
              activeTab === tab.key ? 'text-gray-900 border-b-2 border-gray-900 bg-white' : 'text-gray-500 hover:text-gray-700'
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
                <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">PROFILE</div>
                <h3 class="text-lg font-bold text-gray-900 mb-4">学习档案</h3>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <div class="text-sm text-gray-500">专业</div>
                    <div class="font-medium text-gray-900">{{ analysis.major }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">课程</div>
                    <div class="font-medium text-gray-900">{{ analysis.course }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">年级</div>
                    <div class="font-medium text-gray-900">{{ analysis.grade_level }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">学习目标</div>
                    <div class="font-medium text-gray-900">{{ analysis.learning_goal }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">知识水平</div>
                    <div class="font-medium text-gray-900">{{ analysis.knowledge_level }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">学习风格</div>
                    <div class="font-medium text-gray-900">{{ analysis.learning_style }}</div>
                  </div>
                </div>
              </div>

              <div class="bg-gray-50 rounded-xl p-6">
                <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">LEARNING TREND</div>
                <h3 class="text-lg font-bold text-gray-900 mb-4">本周学习时长</h3>
                <div class="flex items-end justify-between h-40 gap-2">
                  <div
                    v-for="(hours, index) in analysis.weeklyData"
                    :key="index"
                    class="flex-1 flex flex-col items-center gap-2"
                  >
                    <div 
                      class="w-full bg-gray-800 rounded-t-lg transition-all duration-500"
                      :style="{ height: (hours / maxWeeklyHours * 120) + 'px' }"
                    ></div>
                    <span class="text-xs text-gray-500">{{ ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][index].slice(1) }}</span>
                    <span class="text-xs font-medium text-gray-700">{{ hours }}h</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'weakPoints'">
            <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">WEAK POINTS</div>
            <h3 class="text-lg font-bold text-gray-900 mb-4">薄弱环节分析</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div
                v-for="(point, index) in analysis.weakPoints"
                :key="index"
                class="bg-gray-50 border border-gray-200 rounded-xl p-5"
              >
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-10 h-10 bg-gray-200 rounded-xl flex items-center justify-center text-xl">
                    💡
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">薄弱环节 {{ index + 1 }}</div>
                    <div class="text-sm text-gray-500">需要重点关注</div>
                  </div>
                </div>
                <div class="text-lg font-bold text-gray-900">{{ point }}</div>
                <div class="mt-3 text-sm text-gray-600">
                  建议：加强练习，观看相关教学视频
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'suggestions'">
            <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">SUGGESTIONS</div>
            <h3 class="text-lg font-bold text-gray-900 mb-4">学习建议</h3>
            <div class="space-y-4">
              <div
                v-for="(suggestion, index) in analysis.suggestions"
                :key="index"
                class="flex items-start gap-4 p-4 bg-gray-50 rounded-xl border border-gray-200"
              >
                <div class="w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center text-white font-bold">
                  {{ Number(index) + 1 }}
                </div>
                <div>
                  <div class="font-medium text-gray-900">{{ suggestion }}</div>
                  <div class="text-sm text-gray-500 mt-1">预计提升效果：中等</div>
                </div>
                <button class="ml-auto px-4 py-2 bg-gray-800 hover:bg-gray-900 text-white text-sm rounded-lg transition-colors">
                  标记已完成
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>