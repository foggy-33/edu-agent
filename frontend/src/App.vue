<script setup lang="ts">
import { ref } from 'vue'
import HomePage from './components/HomePage.vue'
import AnalyzePage from './components/AnalyzePage.vue'
import GeneratePage from './components/GeneratePage.vue'
import EvaluatePage from './components/EvaluatePage.vue'
import CoursePage from './components/CoursePage.vue'
import ExercisePage from './components/ExercisePage.vue'

type Page = 'home' | 'analyze' | 'generate' | 'evaluate' | 'courses' | 'exercise'

const currentPage = ref<Page>('home')
const sidebarCollapsed = ref(false)

const navItems = [
  { key: 'home' as const, label: '首页', icon: '🏠' },
  { key: 'analyze' as const, label: '学习分析', icon: '📊' },
  { key: 'generate' as const, label: '资源生成', icon: '✨' },
  { key: 'evaluate' as const, label: '学习评估', icon: '📝' },
  { key: 'courses' as const, label: '课程管理', icon: '📚' },
  { key: 'exercise' as const, label: '习题练习', icon: '✏️' },
]

function navigate(page: Page) {
  currentPage.value = page
}
</script>

<template>
  <div class="flex h-screen bg-gray-50 overflow-hidden">
    <aside 
      :class="[
        'bg-white border-r border-gray-200 transition-all duration-300 flex flex-col',
        sidebarCollapsed ? 'w-16' : 'w-64'
      ]"
    >
      <div class="p-4 border-b border-gray-200 flex items-center justify-between">
        <div :class="['flex items-center gap-3', sidebarCollapsed ? 'justify-center w-full' : '']">
          <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-xl font-bold">
            S
          </div>
          <span v-if="!sidebarCollapsed" class="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            智能学习助手
          </span>
        </div>
      </div>

      <nav class="flex-1 p-3 space-y-1">
        <button
          v-for="item in navItems"
          :key="item.key"
          @click="navigate(item.key)"
          :class="[
            'w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200',
            currentPage === item.key
              ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          ]"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed" class="font-medium">{{ item.label }}</span>
          <span 
            v-if="!sidebarCollapsed && currentPage === item.key" 
            class="ml-auto w-2 h-2 bg-white rounded-full"
          ></span>
        </button>
      </nav>

      <div class="p-3 border-t border-gray-200">
        <button 
          @click="sidebarCollapsed = !sidebarCollapsed"
          class="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-gray-600 hover:bg-gray-100 transition-all"
        >
          <span class="text-lg">{{ sidebarCollapsed ? '▶' : '◀' }}</span>
          <span v-if="!sidebarCollapsed" class="font-medium">收起菜单</span>
        </button>
      </div>
    </aside>

    <main class="flex-1 overflow-auto">
      <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div>
          <h1 class="text-xl font-bold text-gray-800">
            {{ navItems.find(n => n.key === currentPage)?.label }}
          </h1>
          <p class="text-sm text-gray-500 mt-1">
            {{ currentPage === 'home' ? '欢迎回来，查看您的学习数据' :
               currentPage === 'analyze' ? '分析您的学习情况，发现薄弱环节' :
               currentPage === 'generate' ? '生成个性化学习资源' :
               currentPage === 'evaluate' ? '评估学习效果，获取改进建议' :
               currentPage === 'courses' ? '管理您的课程和学习进度' :
               '通过习题练习巩固知识，提升技能' }}
          </p>
        </div>
        <div class="flex items-center gap-4">
          <div class="relative">
            <input 
              type="text" 
              placeholder="搜索..." 
              class="w-64 px-4 py-2 pl-10 bg-gray-100 border-none rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
          </div>
          <button class="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">
            🔔
            <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
          <div class="flex items-center gap-3 pl-4 border-l border-gray-200">
            <div class="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center text-white font-bold">
              U
            </div>
            <div class="text-sm">
              <div class="font-medium text-gray-800">用户</div>
              <div class="text-gray-500">demo_user_001</div>
            </div>
          </div>
        </div>
      </header>

      <div class="p-6">
        <HomePage v-if="currentPage === 'home'" @navigate="navigate" />
        <AnalyzePage v-else-if="currentPage === 'analyze'" />
        <GeneratePage v-else-if="currentPage === 'generate'" />
        <EvaluatePage v-else-if="currentPage === 'evaluate'" />
        <CoursePage v-else-if="currentPage === 'courses'" />
        <ExercisePage v-else-if="currentPage === 'exercise'" />
      </div>
    </main>
  </div>
</template>
