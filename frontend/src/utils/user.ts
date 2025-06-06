import { v4 as uuidv4 } from 'uuid'

/**
 * 获取或生成用户ID
 * @returns 用户ID
 */
export function getUserId(): string {
  let userId = localStorage.getItem('mineru_user_id')
  if (!userId) {
    userId = uuidv4()
    localStorage.setItem('mineru_user_id', userId)
  }
  return userId
} 