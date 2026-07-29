<script setup lang="ts">
import { computed, ref } from 'vue'
import { loadSkills, parseSkillText, saveSkills, type ImportedSkill } from '../api/skills'

const skills = ref<ImportedSkill[]>(loadSkills())
const fileInput = ref<HTMLInputElement | null>(null)
const importUrl = ref('')
const importing = ref(false)
const message = ref('')
const error = ref('')

const enabledCount = computed(() => skills.value.filter(skill => skill.enabled).length)

function persist(next: ImportedSkill[]) {
  skills.value = next
  saveSkills(next)
}

function toggleSkill(id: string) {
  persist(skills.value.map(skill => skill.id === id ? { ...skill, enabled: !skill.enabled } : skill))
}

function removeSkill(id: string) {
  const target = skills.value.find(skill => skill.id === id)
  if (!target || target.builtin) return
  if (!window.confirm(`确定删除 Skill“${target.name}”吗？`)) return
  persist(skills.value.filter(skill => skill.id !== id))
}

function addImportedSkill(skill: ImportedSkill) {
  const duplicate = skills.value.find(item =>
    !item.builtin && item.name.toLowerCase() === skill.name.toLowerCase()
  )
  const next = duplicate
    ? skills.value.map(item => item.id === duplicate.id ? { ...skill, id: duplicate.id } : item)
    : [...skills.value, skill]
  persist(next)
  message.value = duplicate ? `已更新 ${skill.name}` : `已导入 ${skill.name}`
  error.value = ''
}

async function importFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (!files.length) return
  importing.value = true
  message.value = ''
  error.value = ''
  try {
    for (const file of files) {
      addImportedSkill(parseSkillText(await file.text(), `文件 · ${file.name}`))
    }
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'Skill 导入失败'
  } finally {
    importing.value = false
    input.value = ''
  }
}

async function importFromUrl() {
  const url = importUrl.value.trim()
  if (!url) return
  if (!/^https:\/\//i.test(url)) {
    error.value = '仅支持 HTTPS 公开地址'
    return
  }
  importing.value = true
  message.value = ''
  error.value = ''
  try {
    const response = await fetch(url, { headers: { Accept: 'text/markdown, application/json, text/plain' } })
    if (!response.ok) throw new Error(`下载失败：HTTP ${response.status}`)
    const text = await response.text()
    addImportedSkill(parseSkillText(text, `URL · ${new URL(url).hostname}`))
    importUrl.value = ''
  } catch (cause) {
    error.value = cause instanceof Error
      ? `${cause.message}。若平台限制跨域访问，请先下载 Skill 文件再导入。`
      : 'URL 导入失败'
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="skill-page">
    <header class="skill-header">
      <div>
        <span class="eyebrow">EXTENSIONS</span>
        <h1>Skill 设置</h1>
        <p>导入其他平台的 Skill，并选择要在首页 AI 对话中应用的能力。</p>
      </div>
      <div class="skill-summary">
        <strong>{{ enabledCount }}</strong>
        <span>个 Skill 已启用</span>
      </div>
    </header>

    <section class="import-panel">
      <div class="import-copy">
        <span class="import-icon">
          <svg viewBox="0 0 24 24"><path d="M12 3v12m0 0-4-4m4 4 4-4M5 19h14" /></svg>
        </span>
        <div>
          <h2>从其他平台导入</h2>
          <p>兼容 SKILL.md、Markdown、TXT 和常见 JSON 导出格式，不执行第三方代码。</p>
        </div>
      </div>
      <div class="import-actions">
        <input ref="fileInput" hidden type="file" multiple accept=".md,.txt,.json,text/markdown,text/plain,application/json" @change="importFiles" />
        <button class="file-button" :disabled="importing" @click="fileInput?.click()">选择文件</button>
        <div class="url-import">
          <input v-model="importUrl" type="url" placeholder="粘贴公开 Skill URL，例如 GitHub Raw" @keydown.enter.prevent="importFromUrl" />
          <button :disabled="importing || !importUrl.trim()" @click="importFromUrl">{{ importing ? '导入中' : '导入' }}</button>
        </div>
      </div>
      <p v-if="message" class="notice success">{{ message }}</p>
      <p v-if="error" class="notice failure">{{ error }}</p>
    </section>

    <section class="skill-list-section">
      <div class="section-heading">
        <div>
          <h2>Skill 列表</h2>
          <p>启用后仍可在首页按次取消应用，避免多个 Skill 指令相互冲突。</p>
        </div>
        <span>{{ skills.length }} 个</span>
      </div>

      <div class="skill-grid">
        <article v-for="skill in skills" :key="skill.id" :class="['skill-card', { enabled: skill.enabled }]">
          <div class="skill-card-head">
            <span class="skill-mark">
              <svg viewBox="0 0 24 24"><path d="M9 4h6v4h4v6h-4v6H9v-6H5V8h4V4Z" /><path d="M9 8h6v6H9z" /></svg>
            </span>
            <button class="toggle" :class="{ active: skill.enabled }" :aria-label="`${skill.enabled ? '停用' : '启用'} ${skill.name}`" @click="toggleSkill(skill.id)">
              <i></i>
            </button>
          </div>
          <div class="skill-title">
            <h3>{{ skill.name }}</h3>
            <span v-if="skill.builtin">内置</span>
          </div>
          <p>{{ skill.description }}</p>
          <div class="instruction-preview">{{ skill.instructions }}</div>
          <footer>
            <span>{{ skill.source }}</span>
            <button v-if="!skill.builtin" @click="removeSkill(skill.id)">删除</button>
          </footer>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.skill-page { width: min(1100px, 100%); margin: 0 auto; color: #202123; }
.skill-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 18px; padding: 26px 28px; border: 1px solid #e5e2f5; border-radius: 22px; background: linear-gradient(125deg,#fff 30%,#f5f3ff); }
.eyebrow { color: #6d5de7; font-size: 10px; font-weight: 750; letter-spacing: .14em; }
.skill-header h1 { margin: 8px 0 6px; font-size: 29px; letter-spacing: -.035em; }
.skill-header p,.section-heading p { margin: 0; color: #777785; font-size: 12px; }
.skill-summary { display: flex; align-items: baseline; gap: 7px; min-width: 150px; padding: 14px 17px; border: 1px solid rgba(109,93,231,.15); border-radius: 15px; background: rgba(255,255,255,.8); }
.skill-summary strong { color: #5b4bcc; font-size: 26px; }
.skill-summary span { color: #777785; font-size: 11px; }
.import-panel { padding: 22px; border: 1px solid #e7e7eb; border-radius: 20px; background: #fff; box-shadow: 0 9px 30px rgba(31,31,35,.04); }
.import-copy { display: flex; align-items: center; gap: 13px; }
.import-icon,.skill-mark { display: grid; place-items: center; flex: 0 0 auto; color: #5b4bcc; background: #f1efff; }
.import-icon { width: 44px; height: 44px; border-radius: 14px; }
.import-icon svg,.skill-mark svg { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.import-copy h2,.section-heading h2 { margin: 0 0 5px; font-size: 17px; }
.import-copy p { margin: 0; color: #777785; font-size: 11px; }
.import-actions { display: grid; grid-template-columns: auto 1fr; gap: 10px; margin-top: 18px; }
.file-button,.url-import button { border: 0; border-radius: 11px; color: #fff; background: #202123; font-size: 12px; font-weight: 650; }
.file-button { min-width: 110px; padding: 10px 16px; }
.url-import { display: flex; gap: 8px; }
.url-import input { flex: 1; min-width: 0; padding: 10px 13px; border: 1px solid #dedee3; border-radius: 11px; outline: none; font-size: 12px; }
.url-import input:focus { border-color: #8d82df; box-shadow: 0 0 0 3px rgba(109,93,231,.09); }
.url-import button { padding: 0 17px; }
button:disabled { opacity: .5; cursor: not-allowed; }
.notice { margin: 12px 0 0; padding: 9px 12px; border-radius: 9px; font-size: 11px; }
.notice.success { color: #315d42; background: #f0f9f3; }
.notice.failure { color: #8b3a3a; background: #fff1f1; }
.skill-list-section { margin-top: 28px; }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 14px; }
.section-heading > span { padding: 5px 10px; border-radius: 999px; color: #666674; background: #f1f1f3; font-size: 10px; }
.skill-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; }
.skill-card { position: relative; padding: 18px; overflow: hidden; border: 1px solid #e6e6ea; border-radius: 18px; background: #fff; transition: border-color .22s ease,transform .22s ease,box-shadow .22s ease; }
.skill-card.enabled { border-color: #d8d3f5; box-shadow: 0 10px 28px rgba(66,55,130,.06); }
.skill-card.enabled::before { content: ''; position: absolute; inset: 0 auto 0 0; width: 3px; background: #6d5de7; }
.skill-card:hover { transform: translateY(-2px); box-shadow: 0 14px 34px rgba(36,31,62,.08); }
.skill-card-head { display: flex; align-items: center; justify-content: space-between; }
.skill-mark { width: 39px; height: 39px; border-radius: 12px; }
.skill-mark svg { width: 20px; height: 20px; }
.toggle { position: relative; width: 39px; height: 22px; padding: 0; border: 0; border-radius: 999px; background: #dddde2; transition: background .2s ease; }
.toggle i { position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.18); transition: transform .2s ease; }
.toggle.active { background: #6d5de7; }
.toggle.active i { transform: translateX(17px); }
.skill-title { display: flex; align-items: center; gap: 7px; margin-top: 14px; }
.skill-title h3 { margin: 0; font-size: 15px; }
.skill-title span { padding: 3px 6px; border-radius: 5px; color: #6254ce; background: #f1efff; font-size: 9px; }
.skill-card > p { min-height: 34px; margin: 7px 0 12px; color: #777785; font-size: 11px; line-height: 1.55; }
.instruction-preview { height: 54px; padding: 10px; overflow: hidden; border-radius: 10px; color: #62616d; background: #f7f7f8; font-size: 10px; line-height: 1.65; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.skill-card footer { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; color: #9a99a4; font-size: 9px; }
.skill-card footer button { padding: 3px 7px; border: 0; border-radius: 6px; color: #8b5555; background: #fff2f2; font-size: 9px; }
@media (max-width:720px) { .skill-header { align-items: stretch; flex-direction: column; } .skill-summary { min-width: 0; } .import-actions { grid-template-columns: 1fr; } .file-button { min-height: 40px; } .skill-grid { grid-template-columns: 1fr; } }
</style>
