<script setup lang="ts">
import { ref } from 'vue'
import type { Course } from '../types'

const courses = ref<Course[]>([
  { id: 1, name: '数据库系统', icon: '🗄️', progress: 75, totalHours: 32, completedHours: 24, status: 'in-progress', lastAccess: '2小时前', difficulty: '中等' },
  { id: 2, name: '数据结构', icon: '📊', progress: 60, totalHours: 40, completedHours: 24, status: 'in-progress', lastAccess: '1天前', difficulty: '困难' },
  { id: 3, name: '算法设计', icon: '🧮', progress: 45, totalHours: 48, completedHours: 21, status: 'in-progress', lastAccess: '3天前', difficulty: '困难' },
  { id: 4, name: '操作系统', icon: '💻', progress: 30, totalHours: 36, completedHours: 11, status: 'in-progress', lastAccess: '1周前', difficulty: '中等' },
  { id: 5, name: '计算机网络', icon: '🌐', progress: 100, totalHours: 30, completedHours: 30, status: 'completed', lastAccess: '2周前', difficulty: '中等' },
  { id: 6, name: '软件工程', icon: '🔧', progress: 0, totalHours: 28, completedHours: 0, status: 'not-started', lastAccess: '未开始', difficulty: '简单' },
])

const activeFilter = ref('all')
const filters = [
  { key: 'all', label: '全部' },
  { key: 'in-progress', label: '进行中' },
  { key: 'completed', label: '已完成' },
  { key: 'not-started', label: '未开始' },
]

const selectedCourse = ref<Course | null>(null)

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
  selectedCourse.value = course
}

function closeModal() {
  selectedCourse.value = null
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">总课程数</div>
        <div class="text-3xl font-bold mt-2">{{ courses.length }}门</div>
      </div>
      <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">已完成</div>
        <div class="text-3xl font-bold mt-2">{{ courses.filter(c => c.status === 'completed').length }}门</div>
      </div>
      <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">进行中</div>
        <div class="text-3xl font-bold mt-2">{{ courses.filter(c => c.status === 'in-progress').length }}门</div>
      </div>
      <div class="bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">总学习时长</div>
        <div class="text-3xl font-bold mt-2">{{ courses.reduce((sum, c) => sum + c.completedHours, 0) }}小时</div>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-lg p-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 class="text-lg font-bold text-gray-800">📚 我的课程</h2>
          <p class="text-sm text-gray-500 mt-1">管理您的学习课程和进度</p>
        </div>
        <div class="flex gap-2">
          <button
            v-for="filter in filters"
            :key="filter.key"
            @click="activeFilter = filter.key"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              activeFilter === filter.key
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="course in courses.filter(c => activeFilter === 'all' || c.status === activeFilter)"
          :key="course.id"
          @click="openCourseDetail(course)"
          class="bg-gray-50 rounded-xl p-5 cursor-pointer hover:bg-gray-100 hover:shadow-lg transition-all group"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="w-14 h-14 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
              {{ course.icon }}
            </div>
            <span :class="['px-3 py-1 rounded-full text-xs font-medium', getStatusClass(course.status)]">
              {{ getStatusLabel(course.status) }}
            </span>
          </div>
          
          <div class="mb-3">
            <h3 class="font-medium text-gray-800 group-hover:text-indigo-600 transition-colors">{{ course.name }}</h3>
            <div class="flex items-center gap-2 mt-1">
              <span :class="['px-2 py-0.5 rounded text-xs', getDifficultyClass(course.difficulty)]">
                {{ course.difficulty }}
              </span>
              <span class="text-xs text-gray-500">{{ course.lastAccess }}</span>
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between text-sm mb-2">
              <span class="text-gray-600">学习进度</span>
              <span class="font-medium text-indigo-600">{{ course.progress }}%</span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                :style="{ width: course.progress + '%' }"
              ></div>
            </div>
            <div class="text-xs text-gray-500 mt-2">{{ course.completedHours }} / {{ course.totalHours }} 小时</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedCourse" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="closeModal">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="bg-gradient-to-br from-indigo-500 to-purple-600 p-6 text-white">
          <div class="flex items-start justify-between">
            <div>
              <div class="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center text-4xl mb-3">
                {{ selectedCourse.icon }}
              </div>
              <h2 class="text-2xl font-bold">{{ selectedCourse.name }}</h2>
              <div class="flex items-center gap-2 mt-2">
                <span :class="['px-3 py-1 rounded-full text-sm', getStatusClass(selectedCourse.status)]">
                  {{ getStatusLabel(selectedCourse.status) }}
                </span>
                <span :class="['px-3 py-1 rounded-full text-sm', getDifficultyClass(selectedCourse.difficulty)]">
                  {{ selectedCourse.difficulty }}
                </span>
              </div>
            </div>
            <button @click="closeModal" class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors">
              ✕
            </button>
          </div>
        </div>

        <div class="p-6">
          <div class="mb-6">
            <h3 class="font-medium text-gray-800 mb-4">📊 学习进度</h3>
            <div class="bg-gray-50 rounded-xl p-4">
              <div class="flex items-center justify-between mb-3">
                <span class="text-gray-600">总体进度</span>
                <span class="text-2xl font-bold text-indigo-600">{{ selectedCourse.progress }}%</span>
              </div>
              <div class="h-4 bg-gray-200 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                  :style="{ width: selectedCourse.progress + '%' }"
                ></div>
              </div>
              <div class="flex justify-between mt-2 text-sm text-gray-500">
                <span>{{ selectedCourse.completedHours }} 小时已完成</span>
                <span>共 {{ selectedCourse.totalHours }} 小时</span>
              </div>
            </div>
          </div>

          <div class="mb-6">
            <h3 class="font-medium text-gray-800 mb-4">📚 课程章节</h3>
            <div class="space-y-3">
              <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 font-bold">1</div>
                <div class="flex-1">
                  <div class="font-medium text-gray-800">关系模型与SQL基础</div>
                  <div class="text-sm text-gray-500">4小时</div>
                </div>
                <span class="text-green-600">✓</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 font-bold">2</div>
                <div class="flex-1">
                  <div class="font-medium text-gray-800">函数依赖与范式</div>
                  <div class="text-sm text-gray-500">6小时</div>
                </div>
                <span class="text-green-600">✓</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div class="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center text-amber-600 font-bold">3</div>
                <div class="flex-1">
                  <div class="font-medium text-gray-800">数据库设计与规范化</div>
                  <div class="text-sm text-gray-500">5小时</div>
                </div>
                <span class="text-amber-600">⏳</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl opacity-50">
                <div class="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center text-gray-400 font-bold">4</div>
                <div class="flex-1">
                  <div class="font-medium text-gray-800">事务与并发控制</div>
                  <div class="text-sm text-gray-500">5小时</div>
                </div>
                <span class="text-gray-400">○</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl opacity-50">
                <div class="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center text-gray-400 font-bold">5</div>
                <div class="flex-1">
                  <div class="font-medium text-gray-800">索引与查询优化</div>
                  <div class="text-sm text-gray-500">6小时</div>
                </div>
                <span class="text-gray-400">○</span>
              </div>
            </div>
          </div>

          <div class="flex gap-3">
            <button class="flex-1 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all">
              🎬 继续学习
            </button>
            <button class="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-all">
              📊 查看分析
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
