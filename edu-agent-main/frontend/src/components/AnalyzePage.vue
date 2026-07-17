<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getLearningStats, getDynamicProfile } from '../api/client'
import { loadUserProfile } from '../api/userProfile'
import type { Course } from '../types'

const props = defineProps<{
  course: Course | null
}>()

const emit = defineEmits<{
  navigate: [page: 'detail']
}>()

const userProfile = loadUserProfile()
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
    const [statsResult, profileResult] = await Promise.all([
      getLearningStats(userProfile.userId, props.course.name),
      getDynamicProfile(userProfile.userId, props.course.name),
    ])

    const stats = statsResult.stats
    const profile = profileResult.profile || {}
    const llmCtx = profile.llm_context || {}

    analysis.value = {
      displayName: stats.display_name || '学习者',
      major: stats.major || '未填写',
      course: stats.course || props.course.name,
      grade_level: stats.grade_level || '未填写',
      school: stats.school || '未填写',
      learning_goal: stats.learning_goal || llmCtx.facts?.learning_goal || '未设定',
      knowledge_level: stats.knowledge_level || llmCtx.facts?.knowledge_level || '待评估',
      learning_style: stats.learning_style || llmCtx.facts?.learning_style || '待分析',
      weak_subjects: stats.weak_subjects || [],
      improvement_areas: stats.improvement_areas || [],
      statistics: {
        totalStudyTime: stats.study_hours + '小时',
        averageScore: stats.correct_rate || 0,
        completedCourses: stats.resource_count || 0,
        studyDays: 0,
      },
      weeklyData: stats.weekly_hours || [0, 0, 0, 0, 0, 0, 0],
      weakPoints: stats.weak_topics || llmCtx.weak_points || [],
      weakPointsDetail: stats.weak_points_detail || [],
      suggestions: stats.suggestions || [],
      radar_metrics: stats.radar_metrics || profile.radar_metrics || llmCtx.radar_metrics || {},
      summary: stats.profile_summary || llmCtx.summary || '',
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析失败'
  } finally {
    loading.value = false
  }
}

const maxWeeklyHours = computed(() => {
  return Math.max(...(analysis.value?.weeklyData || [0]), 1)
})

onMounted(() => {
  handleAnalyze()
})

watch(() => props.course?.name, () => {
  if (props.course) {
    handleAnalyze()
  }
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
            <div class="text-xs text-gray-500 mt-2">本课程累计</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="text-sm text-gray-500 mb-2">掌握率</div>
            <div class="text-2xl font-bold text-gray-900">{{ analysis.statistics.averageScore }}%</div>
            <div class="text-xs text-gray-500 mt-2">错题已掌握比例</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="text-sm text-gray-500 mb-2">学习资料</div>
            <div class="text-2xl font-bold text-gray-900">{{ analysis.statistics.completedCourses }}份</div>
            <div class="text-xs text-gray-500 mt-2">已保存到资料库</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="text-sm text-gray-500 mb-2">错题总数</div>
            <div class="text-2xl font-bold text-gray-900">{{ analysis.weakPoints?.length || 0 }}道</div>
            <div class="text-xs text-gray-500 mt-2">需要重点攻克</div>
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
                <div class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <div class="text-sm text-gray-500">姓名</div>
                      <div class="font-medium text-gray-900">{{ analysis.displayName }}</div>
                    </div>
                    <div>
                      <div class="text-sm text-gray-500">学校</div>
                      <div class="font-medium text-gray-900">{{ analysis.school }}</div>
                    </div>
                    <div>
                      <div class="text-sm text-gray-500">专业</div>
                      <div class="font-medium text-gray-900">{{ analysis.major }}</div>
                    </div>
                    <div>
                      <div class="text-sm text-gray-500">年级</div>
                      <div class="font-medium text-gray-900">{{ analysis.grade_level }}</div>
                    </div>
                    <div>
                      <div class="text-sm text-gray-500">当前课程</div>
                      <div class="font-medium text-gray-900">{{ analysis.course }}</div>
                    </div>
                    <div>
                      <div class="text-sm text-gray-500">知识水平</div>
                      <div class="font-medium text-gray-900">{{ analysis.knowledge_level }}</div>
                    </div>
                  </div>
                  <div class="pt-3 border-t border-gray-200">
                    <div class="text-sm text-gray-500 mb-2">学习目标</div>
                    <div class="font-medium text-gray-900">{{ analysis.learning_goal }}</div>
                  </div>
                  <div class="pt-3 border-t border-gray-200">
                    <div class="text-sm text-gray-500 mb-2">学习风格</div>
                    <div class="flex flex-wrap gap-2">
                      <span 
                        v-for="style in (Array.isArray(analysis.learning_style) ? analysis.learning_style : analysis.learning_style.split('、').filter(Boolean))"
                        :key="style"
                        class="px-2.5 py-1 bg-white text-gray-700 text-xs rounded-lg border border-gray-200"
                      >
                        {{ style }}
                      </span>
                      <span v-if="!analysis.learning_style || analysis.learning_style === '待分析'" class="text-gray-400 text-sm">待分析</span>
                    </div>
                  </div>
                  <div v-if="analysis.improvement_areas && analysis.improvement_areas.length > 0" class="pt-3 border-t border-gray-200">
                    <div class="text-sm text-gray-500 mb-2">提升方向</div>
                    <div class="flex flex-wrap gap-2">
                      <span 
                        v-for="area in analysis.improvement_areas"
                        :key="area"
                        class="px-2.5 py-1 bg-purple-50 text-purple-700 text-xs rounded-lg"
                      >
                        {{ area }}
                      </span>
                    </div>
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
            <h3 class="text-lg font-bold text-gray-900 mb-2">薄弱环节分析</h3>
            <p class="text-sm text-gray-500 mb-6">基于你的错题数据智能分析，找出需要重点攻克的知识模块</p>

            <div v-if="analysis.weakPointsDetail && analysis.weakPointsDetail.length > 0" class="space-y-4">
              <div
                v-for="(point, index) in analysis.weakPointsDetail"
                :key="index"
                class="bg-gray-50 border border-gray-200 rounded-xl p-5"
              >
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <div class="w-12 h-12 bg-gradient-to-br from-orange-400 to-red-500 rounded-xl flex items-center justify-center text-xl text-white font-bold">
                      {{ index + 1 }}
                    </div>
                    <div>
                      <div class="font-bold text-gray-900 text-lg">{{ point.topic }}</div>
                      <div class="text-sm text-gray-500">
                        共 {{ point.total_count }} 道题 · 错 {{ point.total_mistake_count }} 次
                      </div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-2xl font-bold" :class="point.master_rate >= 60 ? 'text-green-600' : 'text-red-500'">
                      {{ point.master_rate }}%
                    </div>
                    <div class="text-xs text-gray-500">掌握率</div>
                  </div>
                </div>

                <div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
                  <div 
                    class="h-full rounded-full transition-all duration-500"
                    :class="point.master_rate >= 80 ? 'bg-green-500' : (point.master_rate >= 60 ? 'bg-yellow-500' : 'bg-red-500')"
                    :style="{ width: point.master_rate + '%' }"
                  ></div>
                </div>

                <div class="grid grid-cols-3 gap-3 mb-4">
                  <div class="bg-white rounded-lg p-3 text-center">
                    <div class="text-lg font-bold text-gray-900">{{ point.total_count }}</div>
                    <div class="text-xs text-gray-500">错题总数</div>
                  </div>
                  <div class="bg-white rounded-lg p-3 text-center">
                    <div class="text-lg font-bold text-red-500">{{ point.unmastered_count }}</div>
                    <div class="text-xs text-gray-500">待复习</div>
                  </div>
                  <div class="bg-white rounded-lg p-3 text-center">
                    <div class="text-lg font-bold text-green-600">{{ point.mastered_count }}</div>
                    <div class="text-xs text-gray-500">已掌握</div>
                  </div>
                </div>

                <div class="flex flex-wrap gap-2 mb-4">
                  <span class="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs rounded-lg">
                    平均难度：{{ point.avg_level }}
                  </span>
                  <span class="px-2.5 py-1 bg-purple-50 text-purple-700 text-xs rounded-lg">
                    主要题型：{{ point.most_type }}
                  </span>
                </div>

                <div class="bg-white border-l-4 border-blue-500 rounded-r-lg p-4">
                  <div class="text-xs font-bold text-blue-600 mb-2">📊 章节薄弱分析</div>
                  <div class="text-sm text-gray-700 leading-relaxed">{{ point.analysis_summary }}</div>
                </div>
              </div>
            </div>

            <div v-else-if="analysis.weakPoints && analysis.weakPoints.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-4">
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

            <div v-else class="text-center py-12">
              <div class="text-4xl mb-3">🎉</div>
              <div class="text-gray-600 font-medium">暂无薄弱环节数据</div>
              <div class="text-gray-400 text-sm mt-1">完成更多练习后，系统会自动分析你的薄弱知识点</div>
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
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>