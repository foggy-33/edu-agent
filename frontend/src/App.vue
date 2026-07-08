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

interface NavItem {
  key: Page
  label: string
  icon: string
}

const navItems: NavItem[] = [
  { key: 'home', label: '个性化资源生成', icon: '○' },
  { key: 'resources', label: '资源库', icon: '□' },
  { key: 'evaluate', label: '学习评估', icon: '✓' },
  { key: 'courses', label: '课程管理', icon: '≡' },
  { key: 'account', label: '个人中心', icon: '◎' },
  { key: 'portrait', label: '画像对话', icon: '◇' },
  { key: 'settings', label: '设置', icon: '⚙' },
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
        <div :class="['flex items-center gap-3', sidebarCollapsed ? 'justify-center w-full' : '']">
          <div class="brand-mark">
            AI
          </div>
          <div v-if="!sidebarCollapsed">
            <div class="brand-name">智学空间</div>
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

      <section v-if="!sidebarCollapsed" class="conversation-history">
        <div class="history-head">
          <span>历史对话</span>
          <button type="button" @click="startNewConversation">新建</button>
        </div>
        <button
          v-for="item in conversationHistory"
          :key="item.id"
          type="button"
          :class="['history-item', selectedHistoryId === item.id ? 'history-item-active' : '']"
          @click="openConversation(item)"
        >
          <span>{{ item.title }}</span>
          <small>{{ new Date(item.createdAt).toLocaleString() }}</small>
        </button>
        <p v-if="!conversationHistory.length" class="history-empty">暂无历史</p>
      </section>

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
        <button
          class="sidebar-logout-button"
          :disabled="loggingOut"
          :title="sidebarCollapsed ? '退出登录' : undefined"
          @click="handleLogout"
        >
          <span>⇥</span>
          <span v-if="!sidebarCollapsed" class="font-medium">{{ loggingOut ? '正在退出...' : '退出登录' }}</span>
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
