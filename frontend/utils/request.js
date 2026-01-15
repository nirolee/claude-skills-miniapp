/**
 * 封装 uni.request
 * 统一的网络请求工具
 */

import { API_BASE_URL, REQUEST_TIMEOUT } from '../config/api.js'

/**
 * 发起 HTTP 请求
 * @param {Object} options - 请求配置
 * @param {String} options.url - 请求路径（相对路径，会自动拼接 BASE_URL）
 * @param {String} options.method - 请求方法 GET/POST/PUT/DELETE
 * @param {Object} options.data - 请求参数
 * @param {Object} options.header - 请求头
 * @param {Boolean} options.loading - 是否显示加载提示
 * @param {String} options.loadingText - 加载提示文字
 * @returns {Promise}
 */
export function request(options = {}) {
  const {
    url = '',
    method = 'GET',
    data = {},
    header = {},
    loading = false,
    loadingText = '加载中...',
    timeout = REQUEST_TIMEOUT
  } = options

  // 显示加载提示
  if (loading) {
    uni.showLoading({
      title: loadingText,
      mask: true
    })
  }

  // 构建完整URL
  const fullUrl = `${API_BASE_URL}${url}`

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      method: method.toUpperCase(),
      data,
      header: {
        'Content-Type': 'application/json',
        ...header
      },
      timeout,
      success: (res) => {
        // 隐藏加载提示
        if (loading) {
          uni.hideLoading()
        }

        // HTTP 状态码判断
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          // 服务器错误
          const errorMsg = res.data?.detail || res.data?.message || `服务器错误 ${res.statusCode}`
          uni.showToast({
            title: errorMsg,
            icon: 'none',
            duration: 2000
          })
          reject(new Error(errorMsg))
        }
      },
      fail: (err) => {
        // 隐藏加载提示
        if (loading) {
          uni.hideLoading()
        }

        // 网络错误
        let errorMsg = '网络请求失败'
        if (err.errMsg) {
          if (err.errMsg.includes('timeout')) {
            errorMsg = '请求超时，请检查网络'
          } else if (err.errMsg.includes('fail')) {
            errorMsg = '网络连接失败'
          }
        }

        uni.showToast({
          title: errorMsg,
          icon: 'none',
          duration: 2000
        })
        reject(new Error(errorMsg))
      }
    })
  })
}

/**
 * GET 请求
 */
export function get(url, params = {}, options = {}) {
  return request({
    url,
    method: 'GET',
    data: params,
    ...options
  })
}

/**
 * POST 请求
 */
export function post(url, data = {}, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

/**
 * PUT 请求
 */
export function put(url, data = {}, options = {}) {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

/**
 * DELETE 请求
 */
export function del(url, data = {}, options = {}) {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  })
}

export default {
  request,
  get,
  post,
  put,
  del
}
