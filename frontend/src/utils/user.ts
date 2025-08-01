// 用户相关工具函数

/**
 * 获取用户ID
 * 在实际应用中，这应该从认证系统或本地存储中获取
 */
export function getUserId(): string {
  // 从localStorage获取用户ID，如果没有则生成一个临时ID
  let userId = localStorage.getItem('userId')
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    localStorage.setItem('userId', userId)
  }
  return userId
}

/**
 * 设置用户ID
 */
export function setUserId(userId: string): void {
  localStorage.setItem('userId', userId)
}

/**
 * 清除用户ID
 */
export function clearUserId(): void {
  localStorage.removeItem('userId')
}

/**
 * 获取用户信息
 */
export function getUserInfo() {
  return {
    id: getUserId(),
    name: localStorage.getItem('userName') || '用户',
    avatar: localStorage.getItem('userAvatar') || ''
  }
}

/**
 * 设置用户信息
 */
export function setUserInfo(userInfo: { name?: string; avatar?: string }) {
  if (userInfo.name) {
    localStorage.setItem('userName', userInfo.name)
  }
  if (userInfo.avatar) {
    localStorage.setItem('userAvatar', userInfo.avatar)
  }
}