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
  <div class="app-shell">
    <aside 
      :class="[
        'app-sidebar',
        sidebarCollapsed ? 'app-sidebar-collapsed' : ''
      ]"
    >
      <div class="app-brand">
        <div :class="['flex items-center gap-3', sidebarCollapsed ? 'justify-center w-full' : '']">
          <div class="brand-mark">
            AI
          </div>
          <div v-if="!sidebarCollapsed">
            <div class="brand-name">StudyFlow</div>
            <div class="brand-caption">智能学习工作台</div>
          </div>
        </div>
      </div>

      <nav class="app-nav">
        <div v-if="!sidebarCollapsed" class="nav-caption">工作台</div>
        <button
          v-for="item in navItems"
          :key="item.key"
          @click="navigate(item.key)"
          :class="[
            'nav-item',
            currentPage === item.key ? 'nav-item-active' : ''
          ]"
          :title="sidebarCollapsed ? item.label : undefined"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed" class="font-medium">{{ item.label }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div v-if="!sidebarCollapsed" class="profile-card">
          <div class="profile-avatar">U</div>
          <div class="min-w-0">
            <div class="profile-name">演示用户</div>
            <div class="profile-id">demo_user_001</div>
          </div>
        </div>
        <button 
          @click="sidebarCollapsed = !sidebarCollapsed"
          class="collapse-button"
        >
          <span>{{ sidebarCollapsed ? '→' : '←' }}</span>
          <span v-if="!sidebarCollapsed" class="font-medium">收起菜单</span>
        </button>
      </div>
    </aside>

    <main class="app-main">
      <header class="app-header">
        <div>
          <h1 class="page-title">
            {{ navItems.find(n => n.key === currentPage)?.label }}
          </h1>
          <p class="page-subtitle">
            {{ currentPage === 'home' ? '欢迎回来，查看您的学习数据' :
               currentPage === 'analyze' ? '分析您的学习情况，发现薄弱环节' :
               currentPage === 'generate' ? '生成个性化学习资源' :
               currentPage === 'evaluate' ? '评估学习效果，获取改进建议' :
               currentPage === 'courses' ? '管理您的课程和学习进度' :
               '通过习题练习巩固知识，提升技能' }}
          </p>
        </div>
        <div class="header-actions">
          <div class="search-box">
            <span>⌕</span>
            <input 
              type="text" 
              placeholder="搜索课程、资源..."
            />
          </div>
          <button class="header-icon-button">
            🔔
            <span class="notification-dot"></span>
          </button>
        </div>
      </header>

      <div class="app-content">
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
