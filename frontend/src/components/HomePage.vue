<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'generate' | 'evaluate' | 'courses']
}>()

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return '上午好'
  if (hour >= 12 && hour < 18) return '下午好'
  return '晚上好'
}

const getTimeTheme = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return 'morning'
  if (hour >= 12 && hour < 18) return 'afternoon'
  return 'evening'
}

const greeting = ref(getGreeting())
const timeTheme = ref(getTimeTheme())

const timeThemeClass = computed(() => {
  switch (timeTheme.value) {
    case 'morning': return 'welcome-morning'
    case 'afternoon': return 'welcome-afternoon'
    case 'evening': return 'welcome-evening'
    default: return 'welcome-afternoon'
  }
})

const stats = ref([
  { label: '已完成课程', value: '12', unit: '门', icon: '📚', trend: '+2 本月', color: 'text-indigo-600' },
  { label: '学习时长', value: '86', unit: '小时', icon: '⏱', trend: '+12% 本周', color: 'text-blue-600' },
  { label: '评估得分', value: '92', unit: '分', icon: '🎯', trend: '+5 分', color: 'text-green-600' },
  { label: '薄弱环节', value: '3', unit: '个', icon: '◎', trend: '待加强', color: 'text-amber-600' },
])

const learningTips = ref([
  { tip: '今日推荐：复习函数依赖和范式判断', time: '刚刚' },
  { tip: '完成了数据库系统章节测试', time: '2小时前' },
  { tip: '生成了新的学习路径', time: '昨天' },
])

const radarData = ref([
  { label: '记忆力', value: 85 },
  { label: '逻辑推理', value: 78 },
  { label: '创造力', value: 72 },
  { label: '注意力', value: 88 },
  { label: '理解力', value: 82 },
  { label: '应用能力', value: 76 },
])

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

const generateRadarPoints = () => {
  const centerX = 100
  const centerY = 100
  const radius = 70
  const numPoints = radarData.value.length
  const points = []
  
  radarData.value.forEach((item, index) => {
    const angle = (Math.PI * 2 * index) / numPoints - Math.PI / 2
    const r = (item.value / 100) * radius
    const x = centerX + r * Math.cos(angle)
    const y = centerY + r * Math.sin(angle)
    points.push(`${x},${y}`)
  })
  
  return points.join(' ')
}

const generateGridLines = () => {
  const centerX = 100
  const centerY = 100
  const numPoints = radarData.value.length
  const lines = []
  
  for (let level = 1; level <= 5; level++) {
    const radius = (level * 70) / 5
    const levelPoints = []
    for (let i = 0; i < numPoints; i++) {
      const angle = (Math.PI * 2 * i) / numPoints - Math.PI / 2
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)
      levelPoints.push(`${x},${y}`)
    }
    lines.push(levelPoints.join(' '))
  }
  
  return lines
}

const generateAxisLines = () => {
  const centerX = 100
  const centerY = 100
  const numPoints = radarData.value.length
  const lines = []
  
  radarData.value.forEach((_, index) => {
    const angle = (Math.PI * 2 * index) / numPoints - Math.PI / 2
    const x = centerX + 70 * Math.cos(angle)
    const y = centerY + 70 * Math.sin(angle)
    lines.push({ x, y })
  })
  
  return lines
}

const generateLabelPositions = () => {
  const centerX = 100
  const centerY = 100
  const numPoints = radarData.value.length
  const positions = []
  
  radarData.value.forEach((item, index) => {
    const angle = (Math.PI * 2 * index) / numPoints - Math.PI / 2
    const r = 85
    const x = centerX + r * Math.cos(angle)
    const y = centerY + r * Math.sin(angle)
    
    let textAnchor = 'middle'
    let dominantBaseline = 'middle'
    
    if (x < centerX - 15) textAnchor = 'end'
    else if (x > centerX + 15) textAnchor = 'start'
    
    if (y < centerY - 15) dominantBaseline = 'hanging'
    else if (y > centerY + 15) dominantBaseline = 'baseline'
    
    positions.push({ x, y, textAnchor, dominantBaseline, label: item.label })
  })
  
  return positions
}

const studyStreak = ref(7)
const todayProgress = ref(72)
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-top-row">
      <div class="dashboard-top-left">
        <section :class="['welcome-panel-small', timeThemeClass]">
          <div>
            <h2>{{ greeting }}，欢迎继续学习</h2>
            <p>今天建议完成数据库系统第 5 章，并进行一次针对性评估。</p>
          </div>
          <div class="goal-ring-small">
            <div class="goal-value">{{ todayProgress }}%</div>
            <div class="goal-label">今日目标</div>
          </div>
        </section>

        <div class="stats-row">
          <article v-for="stat in stats" :key="stat.label" class="stat-card">
            <div class="stat-icon">{{ stat.icon }}</div>
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-row-inner">
              <strong :class="stat.color">{{ stat.value }}<span class="stat-unit">{{ stat.unit }}</span></strong>
              <span>{{ stat.trend }}</span>
            </div>
          </article>
        </div>
      </div>

      <div class="surface activity-panel-tall">
        <div class="section-heading-small">
          <span class="section-kicker">最近动态</span>
          <h2>学习记录</h2>
        </div>
        <div class="activity-list-tall">
          <div v-for="(tip, index) in learningTips" :key="index" class="activity-row-tall">
            <span class="activity-number">{{ index + 1 }}</span>
            <div class="activity-content">
              <strong>{{ tip.tip }}</strong>
              <small>{{ tip.time }}</small>
            </div>
          </div>
        </div>
        <button class="activity-more-btn" @click="emit('navigate', 'analyze')">查看更多 →</button>
      </div>
    </div>

    <div class="dashboard-middle">
      <div class="surface study-panel-wide">
        <div class="section-heading-small">
          <span class="section-kicker">学习习惯</span>
          <h2>本周学习趋势</h2>
        </div>
        <div class="chart-container-wide">
          <div class="chart-bars-wide">
            <div
              v-for="data in weeklyStudyData"
              :key="data.day"
              class="bar-wrapper-wide"
            >
              <div
                class="bar-wide"
                :style="{ height: (data.hours / maxStudyHours * 100) + '%' }"
              >
                <span class="bar-value-wide">{{ data.hours }}h</span>
              </div>
              <span class="bar-label-wide">{{ data.day.slice(1) }}</span>
            </div>
          </div>
        </div>
        <div class="streak-badge-wide">
          <span class="streak-icon">🔥</span>
          <span class="streak-text">连续学习 <strong>{{ studyStreak }}</strong> 天</span>
        </div>
      </div>

      <div class="surface radar-panel-wide">
        <div class="section-heading-small">
          <span class="section-kicker">学习特质</span>
          <h2>能力雷达图</h2>
        </div>
        <div class="radar-container-wide">
          <svg viewBox="0 0 200 200" class="radar-svg-wide">
            <polygon
              v-for="(line, idx) in generateGridLines()"
              :key="`grid-${idx}`"
              :points="line"
              fill="none"
              stroke="#e2e8f0"
              stroke-width="1"
            />
            <line
              v-for="(axis, idx) in generateAxisLines()"
              :key="`axis-${idx}`"
              x1="100"
              y1="100"
              :x2="axis.x"
              :y2="axis.y"
              stroke="#cbd5e1"
              stroke-width="1"
            />
            <polygon
              :points="generateRadarPoints()"
              fill="rgba(99, 102, 241, 0.3)"
              stroke="#6366f1"
              stroke-width="2"
            />
            <circle
              v-for="(point, idx) in generateRadarPoints().split(' ')"
              :key="`point-${idx}`"
              :cx="point.split(',')[0]"
              :cy="point.split(',')[1]"
              r="3"
              fill="#6366f1"
            />
            <text
              v-for="(pos, idx) in generateLabelPositions()"
              :key="`label-${idx}`"
              :x="pos.x"
              :y="pos.y"
              :text-anchor="pos.textAnchor"
              :dominant-baseline="pos.dominantBaseline"
              class="radar-label-wide"
            >{{ pos.label }}</text>
          </svg>
        </div>
        <div class="radar-legend-wide">
          <div v-for="item in radarData" :key="item.label" class="legend-item-wide">
            <span class="legend-label-wide">{{ item.label }}</span>
            <span class="legend-value-wide">{{ item.value }}</span>
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
