<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getDynamicProfile, listDynamicProfiles, smartEvaluate, startQuiz, answerQuiz, finishQuiz, getLearningStats } from '../api/client'
import { loadUserProfile } from '../api/userProfile'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'

defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'account' | 'portrait' | 'resources']
}>()

const userProfile = ref(loadUserProfile())
const profileLoading = ref(false)
const statsLoading = ref(false)
const profileError = ref('')
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const selectedCourse = ref('数据库系统')
const portrait = ref<DynamicProfile | null>(null)
const overallStats = ref<any>(null)
const courseStats = ref<any>(null)

const initials = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')
const activeSubject = computed(() => subjectProfiles.value.find(item => item.course === selectedCourse.value))
const radarMetrics = computed<[string, number][]>(() => {
  const source = portrait.value?.radar_metrics || activeSubject.value?.radar_metrics || courseStats.value?.radar_metrics || {}
  const entries = Object.entries(source) as [string, number][]
  if (entries.length) return entries
  return [
    ['概念理解', 52],
    ['应用迁移', 44],
    ['练习表现', 58],
    ['学习稳定性', 48],
    ['资源偏好', 62],
  ]
})
const radarPoints = computed(() => radarMetrics.value.map(([, value], index) => {
  const total = radarMetrics.value.length
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total
  const radius = 84 * Math.max(0, Math.min(100, Number(value))) / 100
  return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
}).join(' '))
const radarAxes = computed(() => radarMetrics.value.map(([name, value], index) => {
  const total = radarMetrics.value.length
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total
  return {
    name,
    value,
    x: 110 + Math.cos(angle) * 98,
    y: 110 + Math.sin(angle) * 98,
    lineX: 110 + Math.cos(angle) * 88,
    lineY: 110 + Math.sin(angle) * 88,
    anchor: Math.cos(angle) > 0.25 ? 'start' : Math.cos(angle) < -0.25 ? 'end' : 'middle',
  }
}))
const radarRings = computed(() => [20, 40, 60, 80].map(radius => {
  const count = Math.max(radarMetrics.value.length, 3)
  return Array.from({ length: count }, (_, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / count
    return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
  }).join(' ')
}))

const learningStats = computed(() => ({
  totalStudyHours: overallStats.value?.total_study_hours ?? 0,
  completedCourses: overallStats.value?.completed_courses ?? 0,
  correctRate: overallStats.value?.correct_rate ?? 0,
  streakDays: overallStats.value?.streak_days ?? 0,
  totalMistakes: overallStats.value?.total_mistakes ?? 0,
  masteredMistakes: overallStats.value?.mastered_mistakes ?? 0,
  totalResources: overallStats.value?.total_resources ?? 0,
}))

const evalCourse = ref('数据库系统')
const evalMode = ref<'smart' | 'quiz'>('smart')
const evalLoading = ref(false)
const evalResult = ref<any>(null)

const evalQuizQuestions = ref<any[]>([])
const evalQuizCurrentIndex = ref(0)
const evalQuizAnswers = ref<Record<string, string>>({})
const evalQuizFinished = ref(false)

const evaluationStats = computed(() => {
  const totalMistakes = courseStats.value?.total_mistakes ?? 0
  const mastered = courseStats.value?.mastered_mistakes ?? 0
  const correctRate = courseStats.value?.correct_rate ?? 0
  return {
    totalCount: totalMistakes,
    avgScore: correctRate,
    passRate: correctRate,
    mastered,
    unmastered: courseStats.value?.unmastered_mistakes ?? 0,
  }
})

const mockSmartResult = {
  user_id: 'demo_user_001',
  course: '数据库系统',
  profile_summary: {
    knowledge_level: '中级',
    learning_style: '视觉型',
    learning_goal: '考试准备',
  },
  score_summary: { total: 4, correct: 75, wrong: 25, accuracy: 75 },
  weak_points: ['函数依赖', '范式判断'],
  completed_topics: ['关系模型', 'SQL基础'],
  in_progress_topics: ['事务', '索引'],
  analysis: '基于您的学习画像分析：\n- 您的知识水平目前处于中级阶段\n- 学习风格为视觉型，建议多使用图表和思维导图\n- 已掌握的知识点：关系模型、SQL基础\n- 需要加强的知识点：函数依赖、范式判断\n\n综合评估：您的整体表现良好，建议重点复习薄弱环节。',
  next_steps: [
    { title: '重点复习：函数依赖、范式判断', duration: '45分钟', type: 'review' },
    { title: '完成相关章节的练习题', duration: '30分钟', type: 'practice' },
    { title: '观看教学视频加深理解', duration: '20分钟', type: 'video' },
    { title: '进行一次模拟测试检验学习效果', duration: '60分钟', type: 'test' },
  ],
}

async function handleSmartEvaluate() {
  evalLoading.value = true
  evalResult.value = null

  try {
    const response = await smartEvaluate({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
    })
    evalResult.value = response
  } catch {
    evalResult.value = mockSmartResult
  } finally {
    evalLoading.value = false
  }
}

async function handleStartQuiz() {
  evalLoading.value = true
  evalQuizQuestions.value = []
  evalQuizCurrentIndex.value = 0
  evalQuizAnswers.value = {}
  evalQuizFinished.value = false
  evalResult.value = null

  try {
    const response = await startQuiz({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
    })
    evalQuizQuestions.value = [response.question]
    evalQuizCurrentIndex.value = response.current_index
  } catch {
    evalQuizQuestions.value = []
  } finally {
    evalLoading.value = false
  }
}

async function handleQuizAnswer() {
  const currentQuestion = evalQuizQuestions.value[evalQuizCurrentIndex.value]
  if (!currentQuestion) return

  evalLoading.value = true

  try {
    const response = await answerQuiz({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
      question_id: currentQuestion.question_id,
      answer: (evalQuizAnswers.value[currentQuestion.question_id] || '').trim(),
    })

    evalQuizCurrentIndex.value = response.current_index
    if (response.question) {
      evalQuizQuestions.value.push(response.question)
    } else {
      evalQuizFinished.value = true
      await handleFinishQuiz()
    }
  } catch {
  } finally {
    evalLoading.value = false
  }
}

async function handleFinishQuiz() {
  evalLoading.value = true

  try {
    const response = await finishQuiz({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
    })
    evalResult.value = response

    await loadCourseStats(evalCourse.value)
    await loadOverallStats()
  } catch {
  } finally {
    evalLoading.value = false
  }
}

async function loadPortrait(course = selectedCourse.value) {
  profileLoading.value = true
  profileError.value = ''
  try {
    selectedCourse.value = course
    const result = await getDynamicProfile(userProfile.value.userId, course)
    portrait.value = result.profile
    await loadCourseStats(course)
  } catch (err) {
    portrait.value = null
    profileError.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    profileLoading.value = false
  }
}

async function loadOverallStats() {
  try {
    const result = await getLearningStats(userProfile.value.userId)
    overallStats.value = result.stats
  } catch (err) {
    console.error('加载学习统计失败:', err)
  }
}

async function loadCourseStats(course: string) {
  try {
    const result = await getLearningStats(userProfile.value.userId, course)
    courseStats.value = result.stats
  } catch (err) {
    console.error('加载课程统计失败:', err)
  }
}

async function loadProfileOverview() {
  profileLoading.value = true
  statsLoading.value = true
  profileError.value = ''
  try {
    const [profileResult] = await Promise.all([
      listDynamicProfiles(userProfile.value.userId),
      loadOverallStats(),
    ])
    subjectProfiles.value = profileResult.profiles
    if (profileResult.profiles[0]) {
      await loadPortrait(profileResult.profiles[0].course)
    } else {
      await loadPortrait(selectedCourse.value)
    }
  } catch (err) {
    profileError.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    profileLoading.value = false
    statsLoading.value = false
  }
}

onMounted(loadProfileOverview)
</script>

<template>
  <div class="learning-center-container">
    <section class="learning-hero">
      <div>
        <h1>{{ userProfile.name }}的学习中心</h1>
        <p>查看学习进度、学科画像和学习时长统计</p>
      </div>
      <div class="hero-avatar">
        <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
        <span v-else>{{ initials }}</span>
      </div>
    </section>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.totalStudyHours }}</div>
        <div class="stat-label">学习时长 (小时)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.completedCourses }}</div>
        <div class="stat-label">已学课程</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.correctRate }}%</div>
        <div class="stat-label">正确率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.streakDays }}</div>
        <div class="stat-label">连续学习天数</div>
      </div>
    </div>

    <div class="learning-grid">
      <section class="portrait-card">
        <header>
          <h2>学科画像</h2>
          <span class="completion-badge">完成度 {{ portrait?.completion || activeSubject?.completion || 0 }}%</span>
        </header>

        <div class="subject-switcher">
          <button
            v-for="item in subjectProfiles"
            :key="item.course"
            type="button"
            :class="{ active: item.course === selectedCourse }"
            :disabled="profileLoading"
            @click="loadPortrait(item.course)"
          >
            {{ item.course }}
          </button>
          <button v-if="!subjectProfiles.length" type="button" class="active">{{ selectedCourse }}</button>
        </div>

        <div class="portrait-radar-wrap">
          <svg class="portrait-radar" viewBox="0 0 220 220" role="img" aria-label="学科画像雷达图">
            <polygon
              v-for="ring in radarRings"
              :key="ring"
              :points="ring"
              class="radar-ring"
            />
            <line
              v-for="axis in radarAxes"
              :key="axis.name"
              x1="110"
              y1="110"
              :x2="axis.lineX"
              :y2="axis.lineY"
              class="radar-axis"
            />
            <polygon :points="radarPoints" class="radar-area" />
            <polyline :points="radarPoints" class="radar-line" />
            <circle
              v-for="point in radarPoints.split(' ')"
              :key="point"
              :cx="point.split(',')[0]"
              :cy="point.split(',')[1]"
              r="3.2"
              class="radar-point"
            />
            <text
              v-for="axis in radarAxes"
              :key="`${axis.name}-label`"
              :x="axis.x"
              :y="axis.y"
              :text-anchor="axis.anchor"
              class="radar-label"
            >
              {{ axis.name }}
            </text>
          </svg>
        </div>

        <p class="portrait-summary">
          {{ portrait?.llm_context?.summary || activeSubject?.summary || '还没有形成完整画像。完成学习评估或多轮学习问答后，会在这里生成雷达图。' }}
        </p>

        <div class="metric-list">
          <article v-for="[name, value] in radarMetrics" :key="name">
            <div class="metric-head">
              <span>{{ name }}</span>
              <b>{{ value }}</b>
            </div>
            <i><em :style="{ width: `${value}%` }"></em></i>
          </article>
        </div>

        <p v-if="profileError" class="message error">{{ profileError }}</p>
      </section>

      <section class="evaluate-card">
        <header>
          <h2>学习评估</h2>
        </header>

        <div class="evaluate-stats">
          <div class="evaluate-stat">
            <span class="stat-num">{{ evaluationStats.totalCount }}</span>
            <span class="stat-text">错题总数</span>
          </div>
          <div class="evaluate-stat">
            <span class="stat-num">{{ evaluationStats.mastered }}</span>
            <span class="stat-text">已掌握</span>
          </div>
          <div class="evaluate-stat">
            <span class="stat-num">{{ evaluationStats.passRate }}%</span>
            <span class="stat-text">掌握率</span>
          </div>
        </div>

        <div class="evaluate-form">
          <div class="form-item">
            <label>选择课程</label>
            <select v-model="evalCourse">
              <option value="数据库系统">数据库系统</option>
              <option value="数据结构">数据结构</option>
              <option value="算法设计">算法设计</option>
            </select>
          </div>

          <div class="mode-select">
            <button
              @click="evalMode = 'smart'"
              :class="['mode-btn', evalMode === 'smart' ? 'active' : '']"
            >
              智能评估
            </button>
            <button
              @click="evalMode = 'quiz'"
              :class="['mode-btn', evalMode === 'quiz' ? 'active' : '']"
            >
              智能小测
            </button>
          </div>

          <button
            v-if="evalMode === 'smart'"
            @click="handleSmartEvaluate"
            :disabled="evalLoading"
            class="eval-start-btn"
          >
            {{ evalLoading ? '分析中...' : '开始智能评估' }}
          </button>
          <button
            v-else-if="evalMode === 'quiz' && !evalQuizFinished && evalQuizQuestions.length === 0"
            @click="handleStartQuiz"
            :disabled="evalLoading"
            class="eval-start-btn"
          >
            {{ evalLoading ? '加载中...' : '开始智能小测' }}
          </button>
        </div>

        <div v-if="evalQuizQuestions.length > 0 && !evalQuizFinished" class="quiz-area">
          <div class="quiz-progress">
            <span>第 {{ evalQuizCurrentIndex + 1 }} / {{ evalQuizQuestions.length }} 题</span>
            <div class="progress-dots">
              <div
                v-for="(_, index) in evalQuizQuestions"
                :key="index"
                :class="['dot', index === evalQuizCurrentIndex ? 'active' : '']"
              ></div>
            </div>
          </div>
          <div class="quiz-content">
            <div class="quiz-topic">{{ evalQuizQuestions[evalQuizCurrentIndex]?.topic }}</div>
            <div class="quiz-question">{{ evalQuizQuestions[evalQuizCurrentIndex]?.question }}</div>
            <div v-if="evalQuizQuestions[evalQuizCurrentIndex]?.options" class="quiz-options">
              <label
                v-for="(option, idx) in evalQuizQuestions[evalQuizCurrentIndex]?.options"
                :key="idx"
                :class="['option-item', evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id] === String.fromCharCode(65 + idx) ? 'selected' : '']"
              >
                <span class="option-label">{{ String.fromCharCode(65 + idx) }}</span>
                <span class="option-text">{{ option }}</span>
                <input
                  type="radio"
                  :value="String.fromCharCode(65 + idx)"
                  v-model="evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id]"
                  class="hidden"
                />
              </label>
            </div>
            <div v-else>
              <input
                v-model="evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id]"
                type="text"
                class="quiz-input"
                placeholder="请输入答案..."
              />
            </div>
          </div>
          <button
            @click="handleQuizAnswer"
            :disabled="evalLoading || !evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id]"
            class="eval-start-btn"
          >
            {{ evalLoading ? '提交中...' : '下一题' }}
          </button>
        </div>

        <div v-if="evalResult" class="eval-result">
          <div class="result-score">
            <span class="score-label">{{ evalMode === 'smart' ? '智能评估结果' : '测试评估结果' }}</span>
            <span class="score-value">{{ Math.round(evalResult.score_summary.accuracy) }}</span>
            <span class="score-detail">共 {{ evalResult.score_summary.total }} 题，正确 {{ evalResult.score_summary.correct }} 题</span>
          </div>
          <div class="result-bar">
            <div class="bar-fill" :style="{ width: evalResult.score_summary.accuracy + '%' }"></div>
          </div>
          <div class="result-analysis">
            <h4>评估分析</h4>
            <p>{{ evalResult.analysis }}</p>
          </div>
          <div v-if="evalResult.weak_points" class="result-weak">
            <h4>薄弱环节</h4>
            <div class="weak-tags">
              <span v-for="(point, index) in evalResult.weak_points" :key="index" class="weak-tag">{{ point }}</span>
            </div>
          </div>
        </div>

        <div class="eval-history">
          <h4>薄弱知识点</h4>
          <div class="history-list">
            <div v-if="!courseStats?.weak_topics?.length" class="history-empty">
              暂无数据，开始学习后会自动分析薄弱点
            </div>
            <div v-for="(topic, index) in courseStats?.weak_topics || []" :key="index" class="history-item">
              <span class="history-course">{{ topic }}</span>
              <span class="history-score poor">待加强</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.learning-center-container {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1200px;
  margin: 0 auto;
  color: #1f2937;
}

.learning-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 24px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
}

.learning-hero h1 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 600;
  color: #111827;
}

.learning-hero p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.hero-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  color: #fff;
  background: #d1d5db;
  font-size: 22px;
  font-weight: 600;
  overflow: hidden;
  flex-shrink: 0;
}

.hero-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 18px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
}

.learning-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 18px;
  align-items: start;
}

.portrait-card,
.evaluate-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  padding: 20px;
}

.portrait-card header,
.evaluate-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.portrait-card h2,
.evaluate-card h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.completion-badge {
  padding: 4px 10px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  font-weight: 500;
}

.subject-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.subject-switcher button {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  color: #6b7280;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.subject-switcher button:hover {
  border-color: #d1d5db;
  color: #374151;
}

.subject-switcher button.active {
  color: #fff;
  border-color: #111827;
  background: #111827;
}

.subject-switcher button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.portrait-radar-wrap {
  display: grid;
  place-items: center;
  min-height: 260px;
  margin: 8px 0 12px;
  border-radius: 10px;
  background: #f9fafb;
}

.portrait-radar {
  width: min(340px, 100%);
  height: auto;
  overflow: visible;
}

.radar-ring {
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 1;
}

.radar-axis {
  stroke: #e5e7eb;
  stroke-width: 1;
}

.radar-area {
  fill: rgba(55, 65, 81, 0.15);
  stroke: none;
}

.radar-line {
  fill: none;
  stroke: #374151;
  stroke-width: 2.5;
  stroke-linejoin: round;
}

.radar-point {
  fill: #fff;
  stroke: #374151;
  stroke-width: 2;
}

.radar-label {
  fill: #4b5563;
  font-size: 10px;
  font-weight: 500;
}

.portrait-summary {
  margin: 0;
  padding: 12px 14px;
  border-left: 3px solid #d1d5db;
  border-radius: 0 8px 8px 0;
  color: #4b5563;
  background: #f9fafb;
  font-size: 13px;
  line-height: 1.7;
}

.metric-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.metric-list article {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.metric-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metric-list span {
  color: #6b7280;
  font-size: 12px;
  font-weight: 500;
}

.metric-list b {
  color: #1f2937;
  font-size: 13px;
  font-weight: 600;
}

.metric-list i {
  display: block;
  height: 4px;
  overflow: hidden;
  border-radius: 99px;
  background: #e5e7eb;
  font-style: normal;
}

.metric-list em {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #374151;
  font-style: normal;
}

.message {
  padding: 10px 14px;
  border-radius: 8px;
  margin: 14px 0 0;
  font-size: 13px;
}

.message.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.evaluate-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
  padding: 14px;
  border-radius: 10px;
  background: #f9fafb;
}

.evaluate-stat {
  text-align: center;
}

.evaluate-stat .stat-num {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 2px;
}

.evaluate-stat .stat-text {
  font-size: 12px;
  color: #6b7280;
}

.evaluate-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.form-item select {
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  color: #1f2937;
  background: #fff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

.form-item select:focus {
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1);
}

.mode-select {
  display: flex;
  gap: 8px;
}

.mode-btn {
  flex: 1;
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-btn:hover {
  border-color: #d1d5db;
  color: #374151;
}

.mode-btn.active {
  color: #fff;
  border-color: #111827;
  background: #111827;
}

.eval-start-btn {
  width: 100%;
  padding: 10px;
  border: 1px solid #111827;
  border-radius: 8px;
  color: #fff;
  background: #111827;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.eval-start-btn:hover:not(:disabled) {
  background: #1f2937;
  border-color: #1f2937;
}

.eval-start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quiz-area {
  margin-top: 16px;
  padding: 14px;
  border-radius: 10px;
  background: #f9fafb;
}

.quiz-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.progress-dots {
  display: flex;
  gap: 6px;
}

.progress-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
}

.progress-dots .dot.active {
  background: #111827;
}

.quiz-content {
  padding: 14px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.quiz-topic {
  display: inline-block;
  padding: 3px 10px;
  margin-bottom: 10px;
  border-radius: 6px;
  color: #374151;
  background: #f3f4f6;
  font-size: 12px;
  font-weight: 500;
}

.quiz-question {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.6;
}

.quiz-options {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.option-item:hover {
  border-color: #d1d5db;
}

.option-item.selected {
  border-color: #111827;
  background: #f9fafb;
}

.option-label {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  color: #6b7280;
  background: #f3f4f6;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.option-item.selected .option-label {
  color: #fff;
  background: #111827;
}

.option-text {
  flex: 1;
  font-size: 14px;
  color: #1f2937;
}

.hidden {
  display: none;
}

.quiz-input {
  width: 100%;
  margin-top: 14px;
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.quiz-input:focus {
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1);
}

.eval-result {
  margin-top: 16px;
  padding: 16px;
  border-radius: 10px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.result-score {
  text-align: center;
}

.result-score .score-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.result-score .score-value {
  display: block;
  font-size: 48px;
  font-weight: 700;
  color: #111827;
  margin: 6px 0;
}

.result-score .score-detail {
  display: block;
  font-size: 13px;
  color: #6b7280;
}

.result-bar {
  height: 6px;
  margin-top: 14px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #1f2937;
  transition: width 0.5s;
}

.result-analysis {
  margin-top: 14px;
  padding: 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.result-analysis h4,
.result-weak h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.result-analysis p {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
}

.result-weak {
  margin-top: 10px;
  padding: 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.weak-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.weak-tag {
  padding: 4px 10px;
  border-radius: 6px;
  color: #92400e;
  background: #fef3c7;
  font-size: 12px;
  font-weight: 500;
}

.eval-history {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.eval-history h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.history-list {
  display: grid;
  gap: 8px;
}

.history-empty {
  padding: 12px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  background: #f9fafb;
  border-radius: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border-radius: 8px;
  background: #f9fafb;
}

.history-course {
  font-size: 13px;
  color: #1f2937;
  font-weight: 500;
}

.history-score {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 6px;
}

.history-score.excellent {
  color: #166534;
  background: #dcfce7;
}

.history-score.good {
  color: #1e40af;
  background: #dbeafe;
}

.history-score.poor {
  color: #991b1b;
  background: #fee2e2;
}

@media (max-width: 900px) {
  .learning-center-container {
    max-width: none;
  }

  .learning-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .learning-grid {
    grid-template-columns: 1fr;
  }

  .metric-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .stat-value {
    font-size: 22px;
  }
}
</style>
