import { loadUserProfile } from './userProfile'

export interface ImportedSkill {
  id: string
  name: string
  description: string
  instructions: string
  source: string
  enabled: boolean
  builtin?: boolean
  createdAt: string
}

export const SKILLS_UPDATED_EVENT = 'studyflow-skills-updated'
const STORAGE_KEY = 'studyflow_imported_skills_v1'
const MAX_SKILL_SIZE = 120_000
const MAX_INSTRUCTIONS = 20_000

const builtinSkills: ImportedSkill[] = [
  {
    id: 'builtin-socratic-tutor',
    name: '苏格拉底学习导师',
    description: '通过递进提问帮助学习者自己建立概念联系。',
    instructions: '优先通过简短、递进的问题引导学习者思考；每轮只聚焦一个关键点，在给出结论前先检查学习者的理解。',
    source: '智学 AI 内置',
    enabled: false,
    builtin: true,
    createdAt: '2026-01-01T00:00:00.000Z',
  },
  {
    id: 'builtin-exam-coach',
    name: '考试复习教练',
    description: '围绕考点、易错点和迁移练习组织回答。',
    instructions: '回答时先指出核心考点，再给出易错辨析和一道简短迁移练习；内容保持紧凑，适合考试复习。',
    source: '智学 AI 内置',
    enabled: false,
    builtin: true,
    createdAt: '2026-01-01T00:00:00.000Z',
  },
]

function storageKey() {
  const userId = loadUserProfile().userId?.trim() || 'guest'
  return `${STORAGE_KEY}:${userId}`
}

function cleanText(value: unknown): string {
  if (typeof value === 'string') return value.trim()
  if (Array.isArray(value)) return value.map(cleanText).filter(Boolean).join('\n')
  return ''
}

function nestedValue(input: Record<string, any>, paths: string[][]): string {
  for (const path of paths) {
    let current: any = input
    for (const key of path) current = current?.[key]
    const value = cleanText(current)
    if (value) return value
  }
  return ''
}

function parseFrontmatter(content: string) {
  const match = content.match(/^---\s*\r?\n([\s\S]*?)\r?\n---\s*(?:\r?\n|$)/)
  if (!match) return { metadata: {} as Record<string, string>, body: content.trim() }
  const metadata: Record<string, string> = {}
  for (const line of match[1].split(/\r?\n/)) {
    const separator = line.indexOf(':')
    if (separator <= 0) continue
    const key = line.slice(0, separator).trim().toLowerCase()
    const value = line.slice(separator + 1).trim().replace(/^['"]|['"]$/g, '')
    metadata[key] = value
  }
  return { metadata, body: content.slice(match[0].length).trim() }
}

function skillId(name: string) {
  const slug = name.toLowerCase().replace(/[^0-9a-z\u4e00-\u9fff]+/g, '-').replace(/^-|-$/g, '').slice(0, 42)
  return `imported-${slug || 'skill'}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`
}

export function parseSkillText(content: string, source = '本地导入'): ImportedSkill {
  const normalized = content.replace(/^\uFEFF/, '').trim()
  if (!normalized) throw new Error('Skill 文件内容为空')
  if (new Blob([normalized]).size > MAX_SKILL_SIZE) throw new Error('Skill 文件不能超过 120 KB')

  let name = ''
  let description = ''
  let instructions = ''

  if (normalized.startsWith('{')) {
    let parsed: Record<string, any>
    try {
      parsed = JSON.parse(normalized)
    } catch {
      throw new Error('JSON Skill 格式无效')
    }
    name = nestedValue(parsed, [['name'], ['title'], ['skill', 'name'], ['metadata', 'name'], ['manifest', 'name']])
    description = nestedValue(parsed, [['description'], ['summary'], ['skill', 'description'], ['metadata', 'description']])
    instructions = nestedValue(parsed, [
      ['instructions'],
      ['instruction'],
      ['system_prompt'],
      ['systemPrompt'],
      ['prompt'],
      ['prompt_template'],
      ['skill', 'instructions'],
      ['definition', 'instructions'],
      ['config', 'system_prompt'],
    ])
  } else {
    const { metadata, body } = parseFrontmatter(normalized)
    name = metadata.name || metadata.title || body.match(/^#\s+(.+)$/m)?.[1]?.trim() || ''
    description = metadata.description || metadata.summary || ''
    instructions = body.replace(/^#\s+.+(?:\r?\n)+/, '').trim()
  }

  if (!name) throw new Error('未识别到 Skill 名称，请补充 name 或一级标题')
  if (!instructions) throw new Error('未识别到 Skill 指令，请补充 instructions、system_prompt 或正文')
  if (instructions.length > MAX_INSTRUCTIONS) throw new Error('Skill 指令不能超过 20000 字')

  return {
    id: skillId(name),
    name: name.slice(0, 80),
    description: (description || '从其他平台导入的自定义 Skill').slice(0, 240),
    instructions,
    source,
    enabled: true,
    createdAt: new Date().toISOString(),
  }
}

export function loadSkills(): ImportedSkill[] {
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey()) || '[]')
    const imported = Array.isArray(stored) ? stored.filter(item => item?.id && item?.name && item?.instructions) : []
    return builtinSkills.map(skill => {
      const saved = imported.find(item => item.id === skill.id)
      return saved ? { ...skill, enabled: Boolean(saved.enabled) } : skill
    }).concat(imported.filter(item => !item.builtin && !builtinSkills.some(skill => skill.id === item.id)))
  } catch {
    return [...builtinSkills]
  }
}

export function saveSkills(skills: ImportedSkill[]) {
  localStorage.setItem(storageKey(), JSON.stringify(skills))
  window.dispatchEvent(new CustomEvent(SKILLS_UPDATED_EVENT, { detail: skills }))
}

export function enabledSkills() {
  return loadSkills().filter(skill => skill.enabled)
}
