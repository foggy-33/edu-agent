<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'generate' | 'evaluate' | 'courses' | 'exercise']
}>()

const stats = ref([
  { label: '已完成课程', value: 12, icon: '📚', color: 'bg-gradient-to-br from-green-400 to-emerald-600' },
  { label: '学习时长', value: '86小时', icon: '⏰', color: 'bg-gradient-to-br from-blue-400 to-indigo-600' },
  { label: '评估得分', value: '92分', icon: '🏆', color: 'bg-gradient-to-br from-amber-400 to-orange-600' },
  { label: '薄弱环节', value: '3个', icon: '💡', color: 'bg-gradient-to-br from-purple-400 to-pink-600' },
])

const recentCourses = ref([
  { name: '数据库系统', progress: 75, lastAccess: '2小时前', icon: '🗄️' },
  { name: '数据结构', progress: 60, lastAccess: '1天前', icon: '📊' },
  { name: '算法设计', progress: 45, lastAccess: '3天前', icon: '🧮' },
  { name: '操作系统', progress: 30, lastAccess: '1周前', icon: '💻' },
])

const quickActions: { label: string; icon: string; action: 'home' | 'analyze' | 'generate' | 'evaluate' | 'courses' | 'exercise'; color: string }[] = [
  { label: '学习分析', icon: '📊', action: 'analyze', color: 'from-indigo-500 to-purple-600' },
  { label: '资源生成', icon: '✨', action: 'generate', color: 'from-green-500 to-emerald-600' },
  { label: '学习评估', icon: '📝', action: 'evaluate', color: 'from-amber-500 to-orange-600' },
  { label: '课程管理', icon: '📚', action: 'courses', color: 'from-blue-500 to-cyan-600' },
  { label: '习题练习', icon: '✏️', action: 'exercise', color: 'from-pink-500 to-rose-600' },
]

const learningTips = ref([
  { tip: '今日推荐：复习函数依赖和范式判断', time: '刚刚' },
  { tip: '完成了数据库系统章节测试', time: '2小时前' },
  { tip: '生成了新的学习路径', time: '昨天' },
])
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in stats"
        :key="stat.label"
        :class="['p-6 rounded-2xl text-white shadow-lg shadow-black/10', stat.color]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-white/80 text-sm">{{ stat.label }}</p>
            <p class="text-3xl font-bold mt-2">{{ stat.value }}</p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center text-3xl">
            {{ stat.icon }}
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-lg p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800">📚 我的课程</h2>
          <button @click="emit('navigate', 'courses')" class="text-indigo-600 hover:text-indigo-700 font-medium text-sm">
            查看全部 →
          </button>
        </div>
        <div class="space-y-4">
          <div
            v-for="course in recentCourses"
            :key="course.name"
            class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div class="w-12 h-12 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-xl flex items-center justify-center text-2xl">
              {{ course.icon }}
            </div>
            <div class="flex-1">
              <div class="font-medium text-gray-800">{{ course.name }}</div>
              <div class="text-sm text-gray-500">{{ course.lastAccess }}</div>
            </div>
            <div class="w-32">
              <div class="flex items-center justify-between text-sm mb-1">
                <span class="text-gray-600">进度</span>
                <span class="font-medium text-indigo-600">{{ course.progress }}%</span>
              </div>
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                  :style="{ width: course.progress + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4">⚡ 快捷操作</h2>
          <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
            <button
              v-for="action in quickActions"
              :key="action.label"
              @click="emit('navigate', action.action)"
              :class="['p-4 rounded-xl bg-gradient-to-br text-white hover:shadow-lg transition-all hover:scale-105', action.color]"
            >
              <div class="text-2xl mb-2">{{ action.icon }}</div>
              <div class="text-sm font-medium">{{ action.label }}</div>
            </button>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4">📢 学习动态</h2>
          <div class="space-y-4">
            <div
              v-for="(tip, index) in learningTips"
              :key="index"
              class="flex items-start gap-3"
            >
              <div class="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-xs text-indigo-600 flex-shrink-0">
                {{ index + 1 }}
              </div>
              <div class="flex-1">
                <div class="text-sm text-gray-800">{{ tip.tip }}</div>
                <div class="text-xs text-gray-400 mt-1">{{ tip.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl shadow-lg p-8 text-white">
      <div class="flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h2 class="text-2xl font-bold mb-2">🎯 今日学习目标</h2>
          <p class="text-white/80">完成数据库系统第5章的学习和练习</p>
        </div>
        <div class="flex gap-4">
          <button 
            @click="emit('navigate', 'generate')"
            class="px-6 py-3 bg-white text-indigo-600 font-medium rounded-xl hover:bg-gray-50 transition-colors shadow-lg"
          >
            生成学习资源
          </button>
          <button 
            @click="emit('navigate', 'analyze')"
            class="px-6 py-3 bg-white/20 text-white font-medium rounded-xl hover:bg-white/30 transition-colors backdrop-blur"
          >
            分析学习情况
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
