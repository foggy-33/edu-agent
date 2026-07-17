<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getCourses } from '../api/client'
import type { Course } from '../types'

const emit = defineEmits<{
  navigate: [page: 'detail' | 'exercise', course?: Course]
}>()

const courses = ref<Course[]>([])
const loading = ref(false)
const error = ref('')
const activeFilter = ref('all')

const filters = [
  { key: 'all', label: '全部' },
  { key: 'in-progress', label: '进行中' },
  { key: 'completed', label: '已完成' },
  { key: 'not-started', label: '未开始' },
]

const filteredCourses = computed(() =>
  courses.value.filter(course => activeFilter.value === 'all' || course.status === activeFilter.value)
)

const totalHours = computed(() => courses.value.reduce((sum, course) => sum + course.completedHours, 0))

async function loadCourses() {
  loading.value = true
  error.value = ''
  try {
    courses.value = (await getCourses()).courses
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '课程数据加载失败'
  } finally {
    loading.value = false
  }
}

function getStatusClass(status: string) {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-700'
    case 'in-progress': return 'bg-blue-100 text-blue-700'
    case 'not-started': return 'bg-gray-100 text-gray-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'completed': return '已完成'
    case 'in-progress': return '进行中'
    case 'not-started': return '未开始'
    default: return status
  }
}

function getDifficultyClass(difficulty: string) {
  switch (difficulty) {
    case '简单': return 'bg-green-100 text-green-700'
    case '中等': return 'bg-yellow-100 text-yellow-700'
    case '困难': return 'bg-red-100 text-red-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

function openCourseDetail(course: Course) {
  emit('navigate', 'detail', course)
}

onMounted(loadCourses)
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
        <div class="text-gray-500 text-sm">课程总数</div>
        <div class="text-3xl font-bold mt-2 text-gray-900">{{ courses.length }}门</div>
      </div>
      <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
        <div class="text-gray-500 text-sm">已完成</div>
        <div class="text-3xl font-bold mt-2 text-green-600">{{ courses.filter(c => c.status === 'completed').length }}门</div>
      </div>
      <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
        <div class="text-gray-500 text-sm">进行中</div>
        <div class="text-3xl font-bold mt-2 text-blue-600">{{ courses.filter(c => c.status === 'in-progress').length }}门</div>
      </div>
      <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
        <div class="text-gray-500 text-sm">已学时长</div>
        <div class="text-3xl font-bold mt-2 text-gray-900">{{ totalHours }}小时</div>
      </div>
    </div>

    <section class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 class="text-xl font-bold text-gray-900">我的课程</h2>
          <p class="text-sm text-gray-500 mt-1">课程数据来自后端课程目录，练习题可按课程实时生成。</p>
        </div>
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="filter in filters"
            :key="filter.key"
            @click="activeFilter = filter.key"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              activeFilter === filter.key
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="py-16 text-center text-gray-500">正在加载课程...</div>
      <div v-else-if="error" class="py-16 text-center text-red-600">{{ error }}</div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <button
          v-for="course in filteredCourses"
          :key="course.id"
          type="button"
          @click="openCourseDetail(course)"
          class="bg-gray-50 rounded-xl p-5 text-left hover:bg-white hover:shadow-md hover:border-gray-200 border border-transparent transition-all group"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="w-14 h-14 bg-white border border-gray-200 rounded-xl flex items-center justify-center text-sm font-bold text-gray-700 group-hover:scale-105 transition-transform">
              {{ course.icon }}
            </div>
            <span :class="['px-3 py-1 rounded-full text-xs font-medium', getStatusClass(course.status)]">
              {{ getStatusLabel(course.status) }}
            </span>
          </div>

          <h3 class="font-semibold text-gray-900 group-hover:text-gray-700 transition-colors">{{ course.name }}</h3>
          <p class="text-sm text-gray-500 mt-2 min-h-[44px] line-clamp-2">{{ course.description }}</p>

          <div class="flex items-center gap-2 mt-4">
            <span :class="['px-2 py-0.5 rounded text-xs', getDifficultyClass(course.difficulty)]">
              {{ course.difficulty }}
            </span>
            <span class="text-xs text-gray-500">{{ course.lastAccess }}</span>
          </div>

          <div class="mt-4">
            <div class="flex items-center justify-between text-sm mb-2">
              <span class="text-gray-600">学习进度</span>
              <span class="font-medium text-gray-900">{{ course.progress }}%</span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-gray-900 rounded-full transition-all duration-500"
                :style="{ width: course.progress + '%' }"
              ></div>
            </div>
            <div class="flex justify-between text-xs text-gray-500 mt-2">
              <span>{{ course.completedHours }} / {{ course.totalHours }} 小时</span>
              <span>{{ course.questions.length }} 道基础题</span>
            </div>
          </div>
        </button>
      </div>
    </section>
  </div>
</template>
