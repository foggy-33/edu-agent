import type { CollaborativeLearningResponse, CollaborativeResourceType } from '../types'

export const CONVERSATION_HISTORY_EVENT = 'studyflow_conversation_history_updated'

const STORAGE_KEY = 'studyflow_conversation_history'
const MAX_HISTORY = 30

export interface ConversationHistoryItem {
  id: string
  title: string
  question: string
  createdAt: string
  resourceTypes: CollaborativeResourceType[]
  result: CollaborativeLearningResponse
  thinkingSteps: string[]
}

export function loadConversationHistory(): ConversationHistoryItem[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function getConversationHistoryItem(id: string): ConversationHistoryItem | null {
  return loadConversationHistory().find(item => item.id === id) || null
}

export function saveConversationHistoryItem(item: ConversationHistoryItem) {
  const history = loadConversationHistory().filter(existing => existing.id !== item.id)
  const next = [item, ...history].slice(0, MAX_HISTORY)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  window.dispatchEvent(new CustomEvent(CONVERSATION_HISTORY_EVENT, { detail: next }))
}

export function createConversationTitle(question: string) {
  const compact = question.replace(/\s+/g, ' ').trim()
  return compact.length > 24 ? `${compact.slice(0, 24)}...` : compact || '新对话'
}
