<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import AnalyzePage from './components/AnalyzePage.vue'
import EvaluatePage from './components/EvaluatePage.vue'
import CoursePage from './components/CoursePage.vue'
import CourseDetailPage from './components/CourseDetailPage.vue'
import CourseExercisePage from './components/CourseExercisePage.vue'
import ResourceLibrary from './components/ResourceLibrary.vue'

import SettingsPage from './components/SettingsPage.vue'
import UserCenterPage from './components/UserCenterPage.vue'
import AuthPage from './components/AuthPage.vue'
import CollaborativeGeneratePage from './components/CollaborativeGeneratePage.vue'
import PortraitPage from './components/PortraitPage.vue'
import { getCurrentUser, logout, type AuthUser } from './api/auth'
import { CONVERSATION_HISTORY_EVENT, loadConversationHistory, type ConversationHistoryItem } from './api/conversationHistory'
import { loadUserProfile, saveUserProfile, USER_PROFILE_EVENT } from './api/userProfile'
import type { UserProfile } from './types/user'
import type { Course } from './types'

type Page = 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'detail' | 'exercise' | 'resources' | 'settings' | 'account' | 'portrait'

const currentPage = ref<Page>('home')
const sidebarCollapsed = ref(false)
const userProfile = ref(loadUserProfile())
const authUser = ref<AuthUser | null>(null)
const authChecking = ref(true)
const loggingOut = ref(false)
const userInitial = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')
const selectedCourse = ref<Course | null>(null)
const conversationHistory = ref<ConversationHistoryItem[]>(loadConversationHistory())
const selectedHistoryId = ref<string | null>(null)

const navIcons = {
  newChat: ['M12 20h9', 'M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z'],
  files: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z', 'M14 2v6h6', 'M8 13h8', 'M8 17h6'],
  project: ['M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z'],
  evaluate: ['M9 5h6', 'M9 3h6a2 2 0 0 1 2 2v1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h1V5a2 2 0 0 1 2-2Z', 'M8 14l2.2 2.2L16 10.5'],
  portrait: ['M12 3a9 9 0 1 0 9 9', 'M12 3v18', 'M3 12h18', 'M5.6 5.6l12.8 12.8', 'M5.6 18.4 18.4 5.6', 'M8.5 13.5l3 2 4.5-6'],
  user: ['M20 21a8 8 0 0 0-16 0', 'M12 13a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z'],
  model: ['M4 6h16', 'M7 12h10', 'M10 18h4', 'M8 6a2 2 0 1 0 0 .01', 'M16 12a2 2 0 1 0 0 .01', 'M12 18a2 2 0 1 0 0 .01'],
  apps: ['M4 4h6v6H4Z', 'M14 4h6v6h-6Z', 'M4 14h6v6H4Z', 'M14 14h6v6h-6Z'],
  more: ['M5 12h.01', 'M12 12h.01', 'M19 12h.01'],
} as const

interface NavItem {
  key: Page
  label: string
  icon: keyof typeof navIcons
}

const navItems: NavItem[] = [
  { key: 'home', label: '新聊天', icon: 'newChat' },
  { key: 'resources', label: '文件库', icon: 'files' },
  { key: 'courses', label: '课程', icon: 'project' },
  { key: 'evaluate', label: '学习评估', icon: 'evaluate' },
  { key: 'portrait', label: '画像对话', icon: 'portrait' },
  { key: 'account', label: '个人中心', icon: 'user' },
  { key: 'settings', label: '模型设置', icon: 'model' },
]

function navigate(page: Page, course?: Course) {
  if (course) {
    selectedCourse.value = course
  }
  if (page !== 'home') {
    selectedHistoryId.value = null
  }
  currentPage.value = page
}

function startNewConversation() {
  selectedHistoryId.value = null
  currentPage.value = 'home'
}

function handleNavItem(item: NavItem) {
  if (item.key === 'home') {
    startNewConversation()
    return
  }
  navigate(item.key)
}

function openConversation(item: ConversationHistoryItem) {
  selectedHistoryId.value = item.id
  currentPage.value = 'home'
}

function handleUserProfileUpdate(event: Event) {
  userProfile.value = (event as CustomEvent<UserProfile>).detail
}

function handleConversationHistoryUpdate(event: Event) {
  conversationHistory.value = (event as CustomEvent<ConversationHistoryItem[]>).detail
}

function handleAuthenticated(user: AuthUser) {
  authUser.value = user
  const profile: UserProfile = {
    ...loadUserProfile(),
    name: user.display_name,
    userId: user.username,
  }
  saveUserProfile(profile)
  userProfile.value = profile
}

async function handleLogout() {
  if (!window.confirm('确定要退出当前账号吗？')) return
  loggingOut.value = true
  try {
    await logout()
    authUser.value = null
    currentPage.value = 'home'
  } finally {
    loggingOut.value = false
  }
}

onMounted(async () => {
  window.addEventListener(USER_PROFILE_EVENT, handleUserProfileUpdate)
  window.addEventListener(CONVERSATION_HISTORY_EVENT, handleConversationHistoryUpdate)
  const user = await getCurrentUser()
  if (user) handleAuthenticated(user)
  authChecking.value = false
})
onUnmounted(() => {
  window.removeEventListener(USER_PROFILE_EVENT, handleUserProfileUpdate)
  window.removeEventListener(CONVERSATION_HISTORY_EVENT, handleConversationHistoryUpdate)
})
</script>

<template>
  <div v-if="authChecking" class="auth-loading"><div class="brand-mark">AI</div><span>正在进入智学空间...</span></div>
  <AuthPage v-else-if="!authUser" @authenticated="handleAuthenticated" />
  <div v-else class="app-shell">
    <aside 
      :class="[
        'app-sidebar',
        sidebarCollapsed ? 'app-sidebar-collapsed' : ''
      ]"
    >
      <div class="app-brand">
        <div v-if="!sidebarCollapsed" class="brand-name">智学AI</div>
        <div v-else class="brand-mark">AI</div>
        <button
          type="button"
          class="collapse-button"
          :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'"
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          ◧
        </button>
      </div>

      <nav class="app-nav">
        <button
          v-for="item in navItems"
          :key="item.key"
          @click="handleNavItem(item)"
          :class="[
            'nav-item',
            currentPage === item.key ? 'nav-item-active' : ''
          ]"
          :title="sidebarCollapsed ? item.label : undefined"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path v-for="path in navIcons[item.icon]" :key="path" :d="path" />
            </svg>
          </span>
          <span v-if="!sidebarCollapsed" class="font-medium">{{ item.label }}</span>
        </button>
      </nav>

      <section v-if="!sidebarCollapsed" class="conversation-history">
        <div class="history-head">
          <span>最近</span>
        </div>
        <button
          v-for="item in conversationHistory"
          :key="item.id"
          type="button"
          :class="['history-item', selectedHistoryId === item.id ? 'history-item-active' : '']"
          @click="openConversation(item)"
        >
          <span>{{ item.title }}</span>
        </button>
        <p v-if="!conversationHistory.length" class="history-empty">暂无历史</p>
      </section>

      <div class="sidebar-footer">
        <button type="button" class="profile-card" @click="navigate('account')" title="进入个人中心">
          <div class="profile-avatar">
            <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
            <span v-else>{{ userInitial }}</span>
          </div>
          <div v-if="!sidebarCollapsed" class="min-w-0">
            <div class="profile-name">{{ userProfile.name }}</div>
            <div class="profile-id">Plus</div>
          </div>
        </button>
        <button
          class="sidebar-logout-button"
          :disabled="loggingOut"
          :title="loggingOut ? '正在退出...' : '退出登录'"
          @click="handleLogout"
        >
          <span>⇥</span>
        </button>
      </div>
    </aside>

    <main class="app-main">
      <div class="app-content">
        <div v-if="currentPage === 'home'" class="home-generate-center">
          <CollaborativeGeneratePage
            :history-id="selectedHistoryId"
            @conversation-saved="selectedHistoryId = $event"
            @new-conversation="selectedHistoryId = null"
          />
        </div>
        <AnalyzePage 
          v-else-if="currentPage === 'analyze'" 
          :course="selectedCourse"
          @navigate="navigate"
        />
        <CollaborativeGeneratePage v-else-if="currentPage === 'collaborative'" />
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
        <UserCenterPage v-else-if="currentPage === 'account'" @logout="handleLogout" @navigate="navigate" />
        <PortraitPage v-else-if="currentPage === 'portrait'" />
        <SettingsPage v-else-if="currentPage === 'settings'" />
      </div>
    </main>
  </div>
</template>
