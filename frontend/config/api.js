/**
 * API 配置文件
 */

// 开发环境和生产环境的 API 地址
const ENV = {
  // 开发环境 - 本地调试（需要使用微信开发者工具的本地服务器域名设置）
  development: 'http://localhost:8000',

  // 生产环境 - HTTPS 域名（已备案）
  production: 'https://api.liguoqi.site'
}

// 当前环境配置
const isDevelopment = process.env.NODE_ENV === 'development'
const BASE_URL = isDevelopment ? ENV.development : ENV.production

// API 路径前缀
const API_PREFIX = '/api'

// 完整的 API 地址
export const API_BASE_URL = `${BASE_URL}${API_PREFIX}`

// API 端点
export const API_ENDPOINTS = {
  // 技能相关
  SKILLS_LIST: '/skills/',
  SKILL_DETAIL: (id) => `/skills/${id}`,
  SKILL_SHARE: (id) => `/skills/${id}/share`,
  SKILLS_CATEGORIES: '/skills/categories/list',

  // 收藏相关
  FAVORITES_ADD: '/favorites/',
  FAVORITES_REMOVE: '/favorites/',
  FAVORITES_LIST: (userId) => `/favorites/user/${userId}`,
  FAVORITES_CHECK: '/favorites/check',

  // 认证相关
  AUTH_LOGIN: '/auth/login',
  AUTH_USER: (userId) => `/auth/user/${userId}`,
}

// 请求超时时间（毫秒）
export const REQUEST_TIMEOUT = 10000

// 默认分页配置
export const DEFAULT_PAGE_SIZE = 20

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  REQUEST_TIMEOUT,
  DEFAULT_PAGE_SIZE
}
