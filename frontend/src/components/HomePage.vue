<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'generate' | 'evaluate' | 'courses']
}>()

const stats = ref([
  { label: '已完成课程', value: 12, icon: '📚', trend: '+2 本月' },
  { label: '学习时长', value: '86小时', icon: '⏱', trend: '+12% 本周' },
  { label: '评估得分', value: '92分', icon: '↗', trend: '+5 分' },
  { label: '薄弱环节', value: '3个', icon: '◎', trend: '待加强' },
])

const recentCourses = ref([
  { name: '数据库系统', progress: 75, lastAccess: '2小时前', icon: '🗄️' },
  { name: '数据结构', progress: 60, lastAccess: '1天前', icon: '📊' },
  { name: '算法设计', progress: 45, lastAccess: '3天前', icon: '🧮' },
  { name: '操作系统', progress: 30, lastAccess: '1周前', icon: '💻' },
])

const quickActions: { label: string; description: string; icon: string; action: 'home' | 'analyze' | 'generate' | 'evaluate' | 'courses' }[] = [
  { label: '学习分析', description: '查看学习画像', icon: '⌁', action: 'analyze' },
  { label: '资源生成', description: '创建专属资料', icon: '✦', action: 'generate' },
  { label: '学习评估', description: '检验掌握程度', icon: '✓', action: 'evaluate' },
  { label: '课程管理', description: '跟踪课程进度和习题', icon: '▤', action: 'courses' },
]

const learningTips = ref([
  { tip: '今日推荐：复习函数依赖和范式判断', time: '刚刚' },
  { tip: '完成了数据库系统章节测试', time: '2小时前' },
  { tip: '生成了新的学习路径', time: '昨天' },
])
</script>

<template>
  <div class="dashboard">
    <section class="welcome-panel">
      <div>
        <span class="eyebrow">今日学习计划</span>
        <h2>下午好，继续保持你的学习节奏</h2>
        <p>今天建议完成数据库系统第 5 章，并进行一次针对性评估。</p>
        <div class="welcome-actions">
          <button class="primary-action" @click="emit('navigate', 'generate')">生成学习资源</button>
          <button class="secondary-action" @click="emit('navigate', 'analyze')">查看学习分析</button>
        </div>
      </div>
      <div class="goal-ring">
        <div class="goal-value">72%</div>
        <div class="goal-label">今日目标</div>
      </div>
    </section>

    <section class="stats-grid">
      <article v-for="stat in stats" :key="stat.label" class="stat-card">
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-label">{{ stat.label }}</div>
        <div class="stat-row">
          <strong>{{ stat.value }}</strong>
          <span>{{ stat.trend }}</span>
        </div>
      </article>
    </section>

    <section class="dashboard-grid">
      <div class="surface courses-panel">
        <div class="section-heading">
          <div>
            <span class="section-kicker">持续学习</span>
            <h2>我的课程</h2>
          </div>
          <button @click="emit('navigate', 'courses')">查看全部 →</button>
        </div>
        <div class="course-list">
          <button
            v-for="course in recentCourses"
            :key="course.name"
            class="course-row"
            @click="emit('navigate', 'courses')"
          >
            <span class="course-icon">{{ course.icon }}</span>
            <span class="course-copy">
              <strong>{{ course.name }}</strong>
              <small>{{ course.lastAccess }}继续学习</small>
            </span>
            <span class="course-progress">
              <span><b>{{ course.progress }}%</b> 完成</span>
              <span class="progress-track"><i :style="{ width: course.progress + '%' }"></i></span>
            </span>
          </button>
        </div>
      </div>

      <div class="right-column">
        <div class="surface">
          <div class="section-heading compact">
            <div><span class="section-kicker">快速开始</span><h2>常用功能</h2></div>
          </div>
          <div class="quick-grid">
            <button v-for="action in quickActions" :key="action.label" @click="emit('navigate', action.action)" class="quick-action">
              <span class="quick-icon">{{ action.icon }}</span>
              <span><strong>{{ action.label }}</strong><small>{{ action.description }}</small></span>
              <b>→</b>
            </button>
          </div>
        </div>

        <div class="surface activity-panel">
          <div class="section-heading compact">
            <div><span class="section-kicker">最近动态</span><h2>学习记录</h2></div>
          </div>
          <div class="activity-list">
            <div v-for="(tip, index) in learningTips" :key="index" class="activity-row">
              <span>{{ index + 1 }}</span>
              <div><strong>{{ tip.tip }}</strong><small>{{ tip.time }}</small></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
