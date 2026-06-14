<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import HomePage from './components/HomePage.vue'
import AnalyzePage from './components/AnalyzePage.vue'
import GeneratePage from './components/GeneratePage.vue'
import EvaluatePage from './components/EvaluatePage.vue'
import CoursePage from './components/CoursePage.vue'
import ExercisePage from './components/ExercisePage.vue'
import ProfileChatPage from './components/ProfileChatPage.vue'
import SettingsPage from './components/SettingsPage.vue'
import UserCenterPage from './components/UserCenterPage.vue'
import AuthPage from './components/AuthPage.vue'
import CollaborativeGeneratePage from './components/CollaborativeGeneratePage.vue'
import { getCurrentUser, logout, type AuthUser } from './api/auth'
import { loadUserProfile, saveUserProfile, USER_PROFILE_EVENT } from './api/userProfile'
import type { UserProfile } from './types/user'

type Page = 'home' | 'profile' | 'analyze' | 'generate' | 'collaborative' | 'evaluate' | 'courses' | 'exercise' | 'settings' | 'account'

const currentPage = ref<Page>('home')
const sidebarCollapsed = ref(false)
const userProfile = ref(loadUserProfile())
const authUser = ref<AuthUser | null>(null)
const authChecking = ref(true)
const loggingOut = ref(false)
const userInitial = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')

const navItems = [
  { key: 'home' as const, label: '首页', icon: '🏠' },
  { key: 'profile' as const, label: '画像共建', icon: '◎' },
  { key: 'analyze' as const, label: '学习分析', icon: '📊' },
  { key: 'generate' as const, label: '资源生成', icon: '✨' },
  { key: 'collaborative' as const, label: '个性化资源生成', icon: '协' },
  { key: 'evaluate' as const, label: '学习评估', icon: '📝' },
  { key: 'courses' as const, label: '课程管理', icon: '📚' },
  { key: 'exercise' as const, label: '习题练习', icon: '✏️' },
  { key: 'settings' as const, label: '设置', icon: '⚙' },
]

function navigate(page: Page) {
  currentPage.value = page
}

function handleUserProfileUpdate(event: Event) {
  userProfile.value = (event as CustomEvent<UserProfile>).detail
}

function handleAuthenticated(user: AuthUser) {
  authUser.value = user
  const profile = { name: user.display_name, userId: user.username, avatar: '' }
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
  const user = await getCurrentUser()
  if (user) handleAuthenticated(user)
  authChecking.value = false
})
onUnmounted(() => window.removeEventListener(USER_PROFILE_EVENT, handleUserProfileUpdate))
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
      <header class="app-header">
        <div>
          <h1 class="page-title">
            {{ navItems.find(n => n.key === currentPage)?.label }}
          </h1>
          <p class="page-subtitle">
            {{ currentPage === 'home' ? '欢迎回来，查看您的学习数据' :
               currentPage === 'profile' ? '通过自然语言对话持续构建动态学生画像' :
               currentPage === 'analyze' ? '分析您的学习情况，发现薄弱环节' :
               currentPage === 'generate' ? '生成个性化学习资源' :
               currentPage === 'collaborative' ? '多智能体协作生成完整个性化学习资源包' :
               currentPage === 'evaluate' ? '评估学习效果，获取改进建议' :
               currentPage === 'courses' ? '管理您的课程和学习进度' :
               currentPage === 'settings' ? '配置模型服务与接口连接' :
               currentPage === 'account' ? '管理你的名称与头像' :
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
        <ProfileChatPage v-else-if="currentPage === 'profile'" />
        <AnalyzePage v-else-if="currentPage === 'analyze'" />
        <GeneratePage v-else-if="currentPage === 'generate'" />
        <CollaborativeGeneratePage v-else-if="currentPage === 'collaborative'" />
        <EvaluatePage v-else-if="currentPage === 'evaluate'" />
        <CoursePage v-else-if="currentPage === 'courses'" />
        <ExercisePage v-else-if="currentPage === 'exercise'" />
        <SettingsPage v-else-if="currentPage === 'settings'" />
        <UserCenterPage v-else-if="currentPage === 'account'" @logout="handleLogout" />
      </div>
    </main>
  </div>
</template>
