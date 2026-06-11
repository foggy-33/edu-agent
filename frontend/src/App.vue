<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import HomePage from './components/HomePage.vue'
import AnalyzePage from './components/AnalyzePage.vue'
import GeneratePage from './components/GeneratePage.vue'
import EvaluatePage from './components/EvaluatePage.vue'
import CoursePage from './components/CoursePage.vue'
import CourseDetailPage from './components/CourseDetailPage.vue'
import CourseExercisePage from './components/CourseExercisePage.vue'
import ResourceLibrary from './components/ResourceLibrary.vue'

import ProfileChatPage from './components/ProfileChatPage.vue'
import SettingsPage from './components/SettingsPage.vue'
import UserCenterPage from './components/UserCenterPage.vue'
import { loadUserProfile, USER_PROFILE_EVENT } from './api/userProfile'
import type { UserProfile } from './types/user'
import type { Course } from './types'

type Page = 'home' | 'profile' | 'analyze' | 'generate' | 'evaluate' | 'courses' | 'detail' | 'exercise' | 'resources' | 'settings' | 'account'

const currentPage = ref<Page>('home')
const sidebarCollapsed = ref(false)
const userProfile = ref(loadUserProfile())
const userInitial = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')
const selectedCourse = ref<Course | null>(null)

const navItems = [
  { key: 'home' as const, label: '首页', icon: '🏠' },
  { key: 'profile' as const, label: '画像共建', icon: '◎' },
  { key: 'analyze' as const, label: '学习分析', icon: '📊' },
  { key: 'resources' as const, label: '资源库', icon: '📦' },
  { key: 'evaluate' as const, label: '学习评估', icon: '📝' },
  { key: 'courses' as const, label: '课程管理', icon: '📚' },
  { key: 'settings' as const, label: '设置', icon: '⚙' },
]

function navigate(page: Page, course?: Course) {
  if (course) {
    selectedCourse.value = course
  }
  currentPage.value = page
}

function handleUserProfileUpdate(event: Event) {
  userProfile.value = (event as CustomEvent<UserProfile>).detail
}

onMounted(() => window.addEventListener(USER_PROFILE_EVENT, handleUserProfileUpdate))
onUnmounted(() => window.removeEventListener(USER_PROFILE_EVENT, handleUserProfileUpdate))
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
        <button v-if="!sidebarCollapsed" class="profile-card" @click="navigate('account')" title="进入个人中心">
          <div class="profile-avatar">
            <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
            <span v-else>{{ userInitial }}</span>
          </div>
          <div class="min-w-0">
            <div class="profile-name">{{ userProfile.name }}</div>
            <div class="profile-id">{{ userProfile.userId }}</div>
          </div>
        </button>
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
            {{ currentPage === 'detail' ? (selectedCourse?.name || '课程详情') :
               currentPage === 'exercise' ? (selectedCourse?.name + ' - 习题练习' || '习题练习') :
               navItems.find(n => n.key === currentPage)?.label }}
          </h1>
          <p class="page-subtitle">
                {{ currentPage === 'home' ? '欢迎回来，查看您的学习数据' :
                   currentPage === 'profile' ? '通过自然语言对话持续构建动态学生画像' :
                   currentPage === 'analyze' ? '分析您的学习情况，发现薄弱环节' :
                   currentPage === 'generate' ? '生成个性化学习资源' :
                   currentPage === 'resources' ? '管理和查阅所有学习资料' :
                   currentPage === 'evaluate' ? '评估学习效果，获取改进建议' :
                   currentPage === 'courses' ? '管理您的课程、学习进度和习题练习' :
                   currentPage === 'detail' ? '查看课程详情、章节和练习' :
                   currentPage === 'exercise' ? '完成习题练习，检验学习成果' :
                   currentPage === 'settings' ? '配置模型服务与接口连接' :
                   '管理你的名称与头像' }}
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
        <ProfileChatPage v-else-if="currentPage === 'profile'" />
        <AnalyzePage v-else-if="currentPage === 'analyze'" />
        <GeneratePage v-else-if="currentPage === 'generate'" @navigate="navigate" />
        <ResourceLibrary v-else-if="currentPage === 'resources'" @navigate="navigate" />
        <EvaluatePage v-else-if="currentPage === 'evaluate'" />
        <CoursePage v-else-if="currentPage === 'courses'" @navigate="navigate" />
        <CourseDetailPage 
          v-else-if="currentPage === 'detail' && selectedCourse" 
          :course="selectedCourse" 
          @navigate="navigate" 
        />
        <CourseExercisePage 
          v-else-if="currentPage === 'exercise' && selectedCourse" 
          :course="selectedCourse" 
          @navigate="navigate" 
        />
        <SettingsPage v-else-if="currentPage === 'settings'" />
        <UserCenterPage v-else-if="currentPage === 'account'" />
      </div>
    </main>
  </div>
</template>
