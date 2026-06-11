<script setup lang="ts">
import { ref } from 'vue'
import type { Course } from '../types'

const props = defineProps<{
  course: Course
}>()

const emit = defineEmits<{
  navigate: [page: 'courses' | 'exercise']
}>()

const getStatusClass = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-700'
    case 'in-progress': return 'bg-blue-100 text-blue-700'
    case 'not-started': return 'bg-gray-100 text-gray-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'in-progress': return '进行中'
    case 'not-started': return '未开始'
    default: return status
  }
}

const getDifficultyClass = (difficulty: string) => {
  switch (difficulty) {
    case '简单': return 'bg-green-100 text-green-700'
    case '中等': return 'bg-yellow-100 text-yellow-700'
    case '困难': return 'bg-red-100 text-red-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

const chapters = ref([
  { id: 1, name: '关系模型与SQL基础', hours: 4, status: 'completed' },
  { id: 2, name: '函数依赖与范式', hours: 6, status: 'completed' },
  { id: 3, name: '数据库设计与规范化', hours: 5, status: 'current' },
  { id: 4, name: '事务与并发控制', hours: 5, status: 'pending' },
  { id: 5, name: '索引与查询优化', hours: 6, status: 'pending' },
])

const getChapterStatusClass = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-600'
    case 'current': return 'bg-amber-100 text-amber-600'
    default: return 'bg-gray-100 text-gray-400'
  }
}

const getChapterIcon = (status: string) => {
  switch (status) {
    case 'completed': return '✓'
    case 'current': return '⏳'
    default: return '○'
  }
}

const courseSummary = ref([
  { label: '学习次数', value: '12次' },
  { label: '最近学习', value: props.course.lastAccess },
  { label: '平均时长', value: '45分钟/次' },
])
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 flex flex-col">
        <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-xl flex-1 flex flex-col">
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-start gap-4">
              <div class="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center text-3xl flex-shrink-0">
                {{ course.icon }}
              </div>
              <div>
                <div class="flex items-center gap-3 flex-wrap">
                  <h1 class="text-2xl font-bold">{{ course.name }}</h1>
                  <span class="px-3 py-1 bg-white/20 rounded-full text-sm font-medium">
                    {{ course.progress }}%
                  </span>
                </div>
                <div class="flex items-center gap-2 mt-2 flex-wrap">
                  <span :class="['px-3 py-1 rounded-full text-sm font-medium', getStatusClass(course.status)]">
                    {{ getStatusLabel(course.status) }}
                  </span>
                  <span :class="['px-3 py-1 rounded-full text-sm font-medium', getDifficultyClass(course.difficulty)]">
                    {{ course.difficulty }}
                  </span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0">
              <button 
                @click="emit('navigate', 'courses')"
                class="px-5 py-2.5 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-all whitespace-nowrap"
              >
                ← 返回课程列表
              </button>
              <button class="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl font-medium transition-all whitespace-nowrap shadow-lg">
                🎬 继续学习
              </button>
              <button class="px-5 py-2.5 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-all whitespace-nowrap">
                📊 分析
              </button>
            </div>
          </div>
          
          <div class="flex-1 flex flex-col justify-end">
            <div>
              <div class="h-2 bg-white/30 rounded-full overflow-hidden mb-2">
                <div
                  class="h-full bg-white rounded-full transition-all duration-500"
                  :style="{ width: course.progress + '%' }"
                ></div>
              </div>
              <div class="flex justify-between text-xs text-white/80 mb-4">
                <span>{{ course.completedHours }}h / {{ course.totalHours }}h</span>
                <span>总课时 {{ course.totalHours }}小时</span>
              </div>
              <div class="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
                <div v-for="item in courseSummary" :key="item.label" class="text-center">
                  <div class="text-2xl font-bold">{{ item.value }}</div>
                  <div class="text-xs text-white/60 mt-1">{{ item.label }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl shadow-lg p-6 text-white flex flex-col">
        <h3 class="font-bold text-lg mb-4">💡 学习建议</h3>
        <p class="text-white/80 text-sm mb-4 flex-1">
          根据您的学习进度和画像分析，建议您：
        </p>
        <ul class="space-y-3 mb-4">
          <li class="flex items-start gap-2">
            <span class="text-white/60">•</span>
            <span>复习函数依赖和范式判断</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-white/60">•</span>
            <span>完成第三章的练习题</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-white/60">•</span>
            <span>生成个性化学习路径</span>
          </li>
        </ul>
        <button class="w-full py-3 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-all mt-auto">
          🎯 获取完整建议
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h2 class="text-xl font-bold text-gray-800 mb-6">📚 课程章节</h2>
          <div class="space-y-3">
            <div 
              v-for="chapter in chapters" 
              :key="chapter.id"
              class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
            >
              <div :class="['w-10 h-10 rounded-xl flex items-center justify-center font-bold', getChapterStatusClass(chapter.status)]">
                {{ chapter.id }}
              </div>
              <div class="flex-1">
                <div class="font-medium text-gray-800">{{ chapter.name }}</div>
                <div class="text-sm text-gray-500">{{ chapter.hours }}小时</div>
              </div>
              <span :class="['text-lg', chapter.status === 'completed' ? 'text-green-600' : chapter.status === 'current' ? 'text-amber-600' : 'text-gray-400']">
                {{ getChapterIcon(chapter.status) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4">📝 章节习题</h2>
          <div v-if="course.questions.length > 0" class="bg-blue-50 rounded-xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <div class="text-blue-800 font-bold text-lg">共 {{ course.questions.length }} 道题目</div>
                <div class="text-sm text-blue-600">包含单选、多选、判断题</div>
              </div>
              <div class="text-3xl">📝</div>
            </div>
            <button 
              @click="emit('navigate', 'exercise')"
              class="w-full py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all shadow-lg"
            >
              🚀 开始练习
            </button>
          </div>
          <div v-else class="bg-gray-50 rounded-xl p-5 text-center text-gray-500">
            暂无习题
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4">🎯 课程目标</h2>
          <div class="space-y-3">
            <div class="flex items-start gap-3">
              <span class="text-lg text-indigo-500">📌</span>
              <div>
                <div class="font-medium text-gray-800">理解关系数据库基本概念</div>
                <div class="text-sm text-gray-500">掌握关系模型、SQL语言、数据库设计等核心知识</div>
              </div>
            </div>
            <div class="flex items-start gap-3">
              <span class="text-lg text-indigo-500">📌</span>
              <div>
                <div class="font-medium text-gray-800">学会数据库设计与规范化</div>
                <div class="text-sm text-gray-500">掌握函数依赖、范式理论和数据库规范化方法</div>
              </div>
            </div>
            <div class="flex items-start gap-3">
              <span class="text-lg text-indigo-500">📌</span>
              <div>
                <div class="font-medium text-gray-800">掌握事务与并发控制</div>
                <div class="text-sm text-gray-500">理解事务特性、并发控制机制和锁技术</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
