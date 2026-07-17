<script setup lang="ts">
import { computed, ref } from 'vue'
import { saveOnboardingProfile, type OnboardingProfile } from '../api/auth'
import { loadUserProfile, saveUserProfile } from '../api/userProfile'

const emit = defineEmits<{
  completed: [profile: OnboardingProfile]
  skipped: []
}>()

const visible = ref(true)
const currentStep = ref(0)
const loading = ref(false)
const error = ref('')

const gradeLevel = ref('')
const major = ref('')
const school = ref('')
const weakSubjects = ref<string[]>([])
const improvementAreas = ref<string[]>([])
const learningStyle = ref<string[]>([])
const learningGoal = ref('')

const gradeOptions = [
  { value: '大一', label: '大一' },
  { value: '大二', label: '大二' },
  { value: '大三', label: '大三' },
  { value: '大四', label: '大四' },
  { value: '研一', label: '研一' },
  { value: '研二', label: '研二' },
  { value: '研三', label: '研三' },
  { value: '其他', label: '其他' },
]

const subjectOptions = [
  { value: '数据库系统', label: '数据库系统' },
  { value: '数据结构', label: '数据结构' },
  { value: '算法设计', label: '算法设计' },
  { value: '操作系统', label: '操作系统' },
  { value: '计算机网络', label: '计算机网络' },
  { value: '计算机组成原理', label: '计算机组成原理' },
  { value: '软件工程', label: '软件工程' },
  { value: '编译原理', label: '编译原理' },
]

const improvementOptions = [
  { value: '考试成绩', label: '提升考试成绩' },
  { value: '编程能力', label: '增强编程能力' },
  { value: '理论理解', label: '加深理论理解' },
  { value: '实践应用', label: '加强实践应用' },
  { value: '解题思路', label: '培养解题思路' },
  { value: '学习效率', label: '提高学习效率' },
  { value: '知识体系', label: '构建知识体系' },
  { value: '竞赛能力', label: '竞赛/保研准备' },
]

const styleOptions = [
  { value: '视频讲解', label: '🎬 视频讲解' },
  { value: '图文讲义', label: '📖 图文讲义' },
  { value: '思维导图', label: '🧠 思维导图' },
  { value: '练习题', label: '✏️ 练习题' },
  { value: '案例实践', label: '💡 案例实践' },
  { value: '讨论交流', label: '💬 讨论交流' },
  { value: '自主阅读', label: '📚 自主阅读' },
]

const goalOptions = [
  { value: '课程学习', label: '跟上课程进度' },
  { value: '考试复习', label: '应对期末考试' },
  { value: '考研准备', label: '考研复习' },
  { value: '竞赛准备', label: '竞赛/项目' },
  { value: '求职面试', label: '求职面试' },
  { value: '兴趣学习', label: '兴趣驱动' },
]

const totalSteps = 5

const progressPercent = computed(() => ((currentStep.value + 1) / totalSteps) * 100)

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return gradeLevel.value !== ''
    case 1:
      return major.value.trim().length > 0
    case 2:
      return weakSubjects.value.length > 0
    case 3:
      return improvementAreas.value.length > 0 && learningStyle.value.length > 0
    case 4:
      return learningGoal.value !== ''
    default:
      return false
  }
})

function toggleItem(list: string[], value: string) {
  const idx = list.indexOf(value)
  if (idx === -1) {
    list.push(value)
  } else {
    list.splice(idx, 1)
  }
}

function nextStep() {
  if (currentStep.value < totalSteps - 1) {
    currentStep.value += 1
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value -= 1
  }
}

async function completeOnboarding() {
  loading.value = true
  error.value = ''
  try {
    const profile: OnboardingProfile = {
      grade_level: gradeLevel.value,
      major: major.value.trim(),
      weak_subjects: weakSubjects.value,
      improvement_areas: improvementAreas.value,
      learning_style: learningStyle.value,
      learning_goal: learningGoal.value,
      school: school.value.trim(),
    }
    await saveOnboardingProfile(profile)
    const localProfile = loadUserProfile()
    localProfile.major = major.value.trim()
    localProfile.school = school.value.trim()
    localProfile.gradeLevel = gradeLevel.value
    localProfile.weakSubjects = weakSubjects.value
    localProfile.improvementAreas = improvementAreas.value
    localProfile.learningStyle = learningStyle.value
    localProfile.learningGoal = learningGoal.value
    localProfile.onboardingCompleted = true
    saveUserProfile(localProfile)
    visible.value = false
    emit('completed', profile)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '保存失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function skip() {
  visible.value = false
  emit('skipped')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="onboarding-overlay" @click.self="skip">
      <div class="onboarding-dialog">
        <div class="onboarding-header">
          <div class="onboarding-brand">
            <span class="brand-mark">AI</span>
            <div>
              <h3>构建你的学习画像</h3>
              <p>只需 1 分钟，让 AI 更懂你的学习需求</p>
            </div>
          </div>
          <button class="skip-button" type="button" @click="skip">跳过</button>
        </div>

        <div class="onboarding-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <span class="progress-text">{{ currentStep + 1 }} / {{ totalSteps }}</span>
        </div>

        <div class="onboarding-body">
          <div v-if="currentStep === 0" class="step-content">
            <div class="step-icon">🎓</div>
            <h2>你目前的学习阶段是？</h2>
            <p class="step-hint">选择你当前所在的年级</p>
            <div class="option-grid">
              <button
                v-for="opt in gradeOptions"
                :key="opt.value"
                type="button"
                :class="['option-card', gradeLevel === opt.value ? 'selected' : '']"
                @click="gradeLevel = opt.value"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <div v-else-if="currentStep === 1" class="step-content">
            <div class="step-icon">📚</div>
            <h2>你的专业是？</h2>
            <p class="step-hint">填写你的专业名称，让推荐更精准</p>
            <div class="form-group">
              <label>所在院校（选填）</label>
              <input v-model.trim="school" placeholder="例如：XX大学" />
            </div>
            <div class="form-group">
              <label>所学专业 *</label>
              <input v-model.trim="major" placeholder="例如：计算机科学与技术" />
            </div>
          </div>

          <div v-else-if="currentStep === 2" class="step-content">
            <div class="step-icon">📌</div>
            <h2>哪些科目你觉得有困难？</h2>
            <p class="step-hint">可多选，我们会重点关注这些科目</p>
            <div class="option-grid multi">
              <button
                v-for="opt in subjectOptions"
                :key="opt.value"
                type="button"
                :class="['option-card', weakSubjects.includes(opt.value) ? 'selected' : '']"
                @click="toggleItem(weakSubjects, opt.value)"
              >
                <span class="check-mark">{{ weakSubjects.includes(opt.value) ? '✓' : '' }}</span>
                {{ opt.label }}
              </button>
            </div>
          </div>

          <div v-else-if="currentStep === 3" class="step-content">
            <div class="step-icon">🚀</div>
            <h2>你最希望提升哪些方面？</h2>
            <p class="step-hint">可多选（至少选 1 项）</p>
            <div class="option-grid multi">
              <button
                v-for="opt in improvementOptions"
                :key="opt.value"
                type="button"
                :class="['option-card', improvementAreas.includes(opt.value) ? 'selected' : '']"
                @click="toggleItem(improvementAreas, opt.value)"
              >
                <span class="check-mark">{{ improvementAreas.includes(opt.value) ? '✓' : '' }}</span>
                {{ opt.label }}
              </button>
            </div>

            <h2 class="mt-24">你偏好的学习方式是？</h2>
            <p class="step-hint">可多选（至少选 1 项）</p>
            <div class="option-grid multi style-grid">
              <button
                v-for="opt in styleOptions"
                :key="opt.value"
                type="button"
                :class="['option-card', learningStyle.includes(opt.value) ? 'selected' : '']"
                @click="toggleItem(learningStyle, opt.value)"
              >
                <span class="check-mark">{{ learningStyle.includes(opt.value) ? '✓' : '' }}</span>
                {{ opt.label }}
              </button>
            </div>
          </div>

          <div v-else-if="currentStep === 4" class="step-content">
            <div class="step-icon">🎯</div>
            <h2>你当前的学习目标是？</h2>
            <p class="step-hint">选择最符合你现状的一项</p>
            <div class="option-list">
              <button
                v-for="opt in goalOptions"
                :key="opt.value"
                type="button"
                :class="['option-row', learningGoal === opt.value ? 'selected' : '']"
                @click="learningGoal = opt.value"
              >
                <span :class="['radio-dot', learningGoal === opt.value ? 'active' : '']"></span>
                {{ opt.label }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="error" class="onboarding-error">{{ error }}</div>

        <div class="onboarding-footer">
          <button
            v-if="currentStep > 0"
            class="btn-ghost"
            type="button"
            @click="prevStep"
          >
            上一步
          </button>
          <div class="footer-spacer" v-else></div>
          <button
            v-if="currentStep < totalSteps - 1"
            class="btn-primary"
            type="button"
            :disabled="!canProceed"
            @click="nextStep"
          >
            下一步
          </button>
          <button
            v-else
            class="btn-primary"
            type="button"
            :disabled="!canProceed || loading"
            @click="completeOnboarding"
          >
            {{ loading ? '正在保存...' : '完成，开始学习' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(20, 10, 50, 0.6);
  backdrop-filter: blur(4px);
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.onboarding-dialog {
  width: min(560px, 92vw);
  max-height: 90vh;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(60, 30, 120, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.onboarding-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 28px 16px;
  gap: 16px;
}

.onboarding-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.onboarding-brand .brand-mark {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #6d5df2, #a855f7);
  color: #fff;
  font-weight: 800;
  font-size: 14px;
}

.onboarding-brand h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 760;
  color: #25144f;
}

.onboarding-brand p {
  margin: 3px 0 0;
  font-size: 13px;
  color: #80758f;
}

.skip-button {
  padding: 6px 12px;
  border: 0;
  background: transparent;
  color: #80758f;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
}

.skip-button:hover {
  background: #f5f0ff;
  color: #6d5df2;
}

.onboarding-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 28px 16px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #eee9ff;
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6d5df2, #a855f7);
  border-radius: 999px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  font-weight: 700;
  color: #8b75d7;
  min-width: 42px;
  text-align: right;
}

.onboarding-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 28px 20px;
}

.step-content {
  animation: fadeStep 0.3s ease;
}

@keyframes fadeStep {
  from {
    opacity: 0;
    transform: translateX(8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.step-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.step-content h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 760;
  color: #25144f;
}

.step-content .mt-24 {
  margin-top: 24px;
}

.step-hint {
  margin: 6px 0 20px;
  font-size: 14px;
  color: #80758f;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.option-grid.multi {
  grid-template-columns: repeat(2, 1fr);
}

.option-grid.style-grid {
  grid-template-columns: repeat(2, 1fr);
}

.option-card {
  position: relative;
  padding: 14px 16px;
  border: 2px solid #eee9ff;
  border-radius: 14px;
  background: #fff;
  color: #5f526f;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.option-card:hover {
  border-color: #c4b5fd;
  background: #faf8ff;
}

.option-card.selected {
  border-color: #7c5cff;
  background: #f5f0ff;
  color: #5b35c8;
}

.check-mark {
  position: absolute;
  top: 8px;
  right: 10px;
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #7c5cff;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.2s;
}

.option-card.selected .check-mark {
  opacity: 1;
  transform: scale(1);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #5f526f;
}

.form-group input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 2px solid #e7ddff;
  border-radius: 12px;
  font-size: 14px;
  color: #241d35;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1);
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 2px solid #eee9ff;
  border-radius: 14px;
  background: #fff;
  color: #5f526f;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.option-row:hover {
  border-color: #c4b5fd;
  background: #faf8ff;
}

.option-row.selected {
  border-color: #7c5cff;
  background: #f5f0ff;
  color: #5b35c8;
}

.radio-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #d4c5ff;
  transition: all 0.2s;
  flex-shrink: 0;
}

.radio-dot.active {
  border-color: #7c5cff;
  background: #7c5cff;
  box-shadow: inset 0 0 0 4px #fff;
}

.onboarding-error {
  padding: 12px 20px;
  margin: 0 28px;
  border-radius: 10px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 13px;
}

.onboarding-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 18px 28px 24px;
  border-top: 1px solid #f5f0ff;
}

.footer-spacer {
  width: 80px;
}

.btn-ghost {
  padding: 12px 20px;
  border: 0;
  background: transparent;
  color: #80758f;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  border-radius: 12px;
  transition: background 0.2s;
}

.btn-ghost:hover {
  background: #f5f0ff;
  color: #6d5df2;
}

.btn-primary {
  padding: 12px 28px;
  border: 0;
  background: linear-gradient(135deg, #6d5df2, #9d6cff);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(109, 93, 242, 0.25);
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(109, 93, 242, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

@media (max-width: 480px) {
  .option-grid,
  .option-grid.multi,
  .option-grid.style-grid {
    grid-template-columns: 1fr;
  }
}
</style>
