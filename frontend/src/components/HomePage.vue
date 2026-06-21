<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { loadUserProfile } from './../api/userProfile'
import { getDynamicProfile } from './../api/client'
import type { DynamicProfile } from './../types/profile'

const emit = defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'account']
}>()

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return '上午好'
  if (hour >= 12 && hour < 18) return '下午好'
  return '晚上好'
}

const greeting = ref(getGreeting())
const showSplash = ref(false)

const weeklyStudyData = ref([
  { day: '周一', hours: 3.5 },
  { day: '周二', hours: 2.8 },
  { day: '周三', hours: 4.2 },
  { day: '周四', hours: 1.5 },
  { day: '周五', hours: 3.0 },
  { day: '周六', hours: 5.5 },
  { day: '周日', hours: 4.0 },
])

const maxStudyHours = computed(() => Math.max(...weeklyStudyData.value.map(d => d.hours)))

const studyStreak = ref(7)
const todayProgress = ref(72)

const portrait = ref<DynamicProfile | null>(null)
const portraitLoading = ref(false)

interface AvatarTag {
  label: string
  value: string
  icon: string
  color: string
  category: string
}

const avatarTags = computed<AvatarTag[]>(() => {
  if (!portrait.value) return []
  
  const tags: AvatarTag[] = []
  const dims = portrait.value.dimensions || {}
  
  const iconMap: Record<string, string> = {
    '专业与年级': '🎓',
    '学习目标': '🎯',
    '知识基础': '📚',
    '认知风格': '🧠',
    '学习偏好': '⚡',
    '时间安排': '⏰',
    '学习动机': '🔥',
    '能力水平': '💪'
  }
  
  const colorMap = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#10b981', '#3b82f6', '#f59e0b', '#14b8a6']
  
  Object.entries(dims).forEach(([key, dimension], index) => {
    if (dimension.value) {
      const displayValue = Array.isArray(dimension.value) ? dimension.value.slice(0, 2).join('、') : String(dimension.value)
      const confidence = dimension.confidence || 0
      
      tags.push({
        label: key,
        value: displayValue.length > 10 ? displayValue.slice(0, 10) + '…' : displayValue,
        icon: iconMap[key] || '📊',
        color: colorMap[index % colorMap.length],
        category: confidence >= 0.8 ? '核心' : confidence >= 0.5 ? '重要' : '基础'
      })
    }
  })
  
  return tags
})

const coreTags = computed(() => avatarTags.value.filter(t => t.category === '核心'))
const importantTags = computed(() => avatarTags.value.filter(t => t.category === '重要'))
const basicTags = computed(() => avatarTags.value.filter(t => t.category === '基础'))

async function loadPortrait() {
  portraitLoading.value = true
  try {
    const userProfile = loadUserProfile()
    const result = await getDynamicProfile(userProfile.userId)
    portrait.value = result.profile
  } catch (err) {
    console.error('加载画像失败', err)
    portrait.value = null
  } finally {
    portraitLoading.value = false
  }
}

onMounted(() => {
  const justLoggedIn = localStorage.getItem('justLoggedIn')
  if (justLoggedIn === 'true') {
    showSplash.value = true
    localStorage.removeItem('justLoggedIn')
    setTimeout(() => {
      showSplash.value = false
    }, 2500)
  }
  loadPortrait()
})
</script>

<template>
  <div class="dashboard">
    <Transition name="splash">
      <div v-if="showSplash" class="splash-screen">
        <div class="splash-content">
          <div class="splash-logo">
            <span class="logo-icon">AI</span>
          </div>
          <div class="splash-text">
            <h1>{{ greeting }}，欢迎回来</h1>
            <p>正在准备您的学习环境...</p>
          </div>
          <div class="splash-progress">
            <div class="progress-bar-full">
              <div class="progress-fill-full"></div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <div class="dashboard-main">
      <div class="surface study-panel-full">
        <div class="study-header-row">
          <div class="section-heading-small">
            <span class="section-kicker">学习习惯</span>
            <h2>本周学习趋势</h2>
          </div>
          <div class="study-stats-row">
            <div class="streak-badge">
              <span class="streak-icon">🔥</span>
              <span class="streak-text">连续学习 <strong>{{ studyStreak }}</strong> 天</span>
            </div>
            <div class="daily-progress">
              <span class="progress-label">今日目标</span>
              <div class="mini-progress-bar">
                <div class="mini-progress-fill" :style="{ width: todayProgress + '%' }"></div>
              </div>
              <span class="progress-value">{{ todayProgress }}%</span>
            </div>
          </div>
        </div>
        <div class="chart-container-full">
          <div class="chart-bars-full">
            <div
              v-for="data in weeklyStudyData"
              :key="data.day"
              class="bar-wrapper-full"
            >
              <div
                class="bar-full"
                :style="{ height: (Math.max(data.hours / maxStudyHours * 100, 20)) + '%' }"
              >
                <span class="bar-value-full">{{ data.hours }}h</span>
              </div>
              <span class="bar-label-full">{{ data.day.slice(1) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="surface portrait-panel-home">
        <div class="section-heading-small">
          <span class="section-kicker">学习画像</span>
          <h2>我的标签</h2>
          <button class="view-portrait-btn" @click="emit('navigate', 'account')">查看详情 →</button>
        </div>
        <div v-if="portraitLoading" class="portrait-loading">
          <div class="loading-spinner"></div>
          <p>加载画像中...</p>
        </div>
        <div v-else class="portrait-tags-container">
          <div v-if="coreTags.length > 0" class="tags-group-home">
            <div class="tags-label-home">✨ 核心</div>
            <div class="tags-row-home">
              <span 
                v-for="tag in coreTags" 
                :key="tag.label"
                class="portrait-tag-home core-tag-home"
                :style="{ '--tag-color': tag.color }"
              >
                {{ tag.icon }} {{ tag.value }}
              </span>
            </div>
          </div>
          <div v-if="importantTags.length > 0" class="tags-group-home">
            <div class="tags-label-home">📌 重要</div>
            <div class="tags-row-home">
              <span 
                v-for="tag in importantTags" 
                :key="tag.label"
                class="portrait-tag-home important-tag-home"
                :style="{ '--tag-color': tag.color }"
              >
                {{ tag.icon }} {{ tag.value }}
              </span>
            </div>
          </div>
          <div v-if="basicTags.length > 0" class="tags-group-home">
            <div class="tags-label-home">📋 基础</div>
            <div class="tags-row-home">
              <span 
                v-for="tag in basicTags" 
                :key="tag.label"
                class="portrait-tag-home basic-tag-home"
              >
                {{ tag.icon }} {{ tag.value }}
              </span>
            </div>
          </div>
          <div v-if="avatarTags.length === 0" class="empty-tags-home">
            <p>暂无画像数据</p>
            <small>开始学习后会自动生成</small>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-bottom">
      <div class="surface assessment-panel-new">
        <div class="section-heading-bottom">
          <div>
            <span class="section-kicker">评估概览</span>
            <h2>最近评估记录</h2>
          </div>
          <button @click="emit('navigate', 'evaluate')">查看详情 →</button>
        </div>
        <div class="assessment-list-new">
          <div class="assessment-item-new">
            <div class="assessment-info">
              <span class="assessment-course">数据库系统</span>
              <span class="assessment-date">2小时前</span>
            </div>
            <div class="assessment-score high">95分</div>
          </div>
          <div class="assessment-item-new">
            <div class="assessment-info">
              <span class="assessment-course">数据结构</span>
              <span class="assessment-date">1天前</span>
            </div>
            <div class="assessment-score medium">78分</div>
          </div>
          <div class="assessment-item-new">
            <div class="assessment-info">
              <span class="assessment-course">算法设计</span>
              <span class="assessment-date">3天前</span>
            </div>
            <div class="assessment-score low">65分</div>
          </div>
        </div>
      </div>

      <div class="surface progress-panel-new">
        <div class="section-heading-bottom">
          <div>
            <span class="section-kicker">学习进度</span>
            <h2>课程完成情况</h2>
          </div>
          <button @click="emit('navigate', 'courses')">查看全部 →</button>
        </div>
        <div class="progress-list-new">
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">🗄️</span>
              <span class="progress-name">数据库系统</span>
              <span class="progress-percent">75%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 75%"></div>
            </div>
          </div>
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">📊</span>
              <span class="progress-name">数据结构</span>
              <span class="progress-percent">60%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 60%"></div>
            </div>
          </div>
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">🧮</span>
              <span class="progress-name">算法设计</span>
              <span class="progress-percent">45%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 45%"></div>
            </div>
          </div>
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">💻</span>
              <span class="progress-name">操作系统</span>
              <span class="progress-percent">30%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 30%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
