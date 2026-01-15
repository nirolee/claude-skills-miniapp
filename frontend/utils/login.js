/**
 * 微信登录相关工具
 */

import { post } from './request.js'
import { API_ENDPOINTS } from '../config/api.js'

/**
 * 微信登录
 * @returns {Promise<Object>} 用户信息
 */
export async function wxLogin() {
  try {
    // 1. 调用微信登录获取 code
    const loginRes = await new Promise((resolve, reject) => {
      uni.login({
        provider: 'weixin',
        success: resolve,
        fail: reject
      })
    })

    if (!loginRes.code) {
      throw new Error('获取登录凭证失败')
    }

    // 2. 获取用户信息（昵称、头像等）
    let userInfo = null
    try {
      const userInfoRes = await new Promise((resolve, reject) => {
        uni.getUserProfile({
          desc: '用于完善用户资料',
          success: resolve,
          fail: reject
        })
      })
      userInfo = userInfoRes.userInfo
    } catch (error) {
      console.log('用户拒绝授权获取用户信息', error)
      // 不阻断登录流程，继续使用默认信息
    }

    // 3. 发送 code 到后端换取 openid 和 token
    const loginData = {
      code: loginRes.code,
      nickname: userInfo?.nickName,
      avatar_url: userInfo?.avatarUrl,
      gender: userInfo?.gender || 0,
      city: userInfo?.city,
      province: userInfo?.province
    }

    const response = await post('/auth/login', loginData)

    // 4. 保存用户信息到本地
    uni.setStorageSync('user', response)
    uni.setStorageSync('token', response.token)
    uni.setStorageSync('user_id', response.user_id)

    // 5. 返回用户信息
    return response
  } catch (error) {
    console.error('登录失败', error)
    uni.showToast({
      title: '登录失败，请重试',
      icon: 'none'
    })
    throw error
  }
}

/**
 * 检查登录状态
 * @returns {Boolean} 是否已登录
 */
export function checkLogin() {
  const user = uni.getStorageSync('user')
  const token = uni.getStorageSync('token')
  return !!(user && token)
}

/**
 * 获取当前用户信息
 * @returns {Object|null} 用户信息
 */
export function getCurrentUser() {
  return uni.getStorageSync('user')
}

/**
 * 获取当前用户 ID
 * @returns {Number|null} 用户 ID
 */
export function getCurrentUserId() {
  return uni.getStorageSync('user_id')
}

/**
 * 退出登录
 */
export function logout() {
  uni.removeStorageSync('user')
  uni.removeStorageSync('token')
  uni.removeStorageSync('user_id')

  uni.showToast({
    title: '已退出登录',
    icon: 'success'
  })
}

/**
 * 要求用户登录（如果未登录则跳转到个人中心）
 * @returns {Promise<Boolean>} 是否已登录
 */
export async function requireLogin() {
  if (checkLogin()) {
    return true
  }

  const res = await new Promise((resolve) => {
    uni.showModal({
      title: '提示',
      content: '此操作需要登录，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.switchTab({
            url: '/pages/profile/profile',
            success: () => resolve(false),
            fail: () => resolve(false)
          })
        } else {
          resolve(false)
        }
      }
    })
  })

  return false
}

export default {
  wxLogin,
  checkLogin,
  getCurrentUser,
  getCurrentUserId,
  logout,
  requireLogin
}
