import type { UserProfile } from '../types/user'

const STORAGE_KEY = 'studyflow_user_profile'
export const USER_PROFILE_EVENT = 'studyflow-user-profile-updated'

export const defaultUserProfile: UserProfile = {
  name: '演示用户',
  userId: 'demo_user_001',
  avatar: '',
  phone: '',
  email: '',
  school: '',
  major: ''
}

export function loadUserProfile(): UserProfile {
  try {
    return { ...defaultUserProfile, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') }
  } catch {
    return { ...defaultUserProfile }
  }
}

export function saveUserProfile(profile: UserProfile) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
  window.dispatchEvent(new CustomEvent(USER_PROFILE_EVENT, { detail: profile }))
}
