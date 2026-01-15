/**
 * 技能相关 API
 */

import { get, post, del } from '../utils/request.js'
import { API_ENDPOINTS, DEFAULT_PAGE_SIZE } from '../config/api.js'

/**
 * 获取技能列表
 * @param {Object} params - 查询参数
 * @param {String} params.category - 分类 (可选)
 * @param {String} params.search - 搜索关键词 (可选)
 * @param {Boolean} params.is_official - 是否官方 (可选)
 * @param {String} params.order_by - 排序字段 (可选: created_at, stars, favorite_count)
 * @param {Boolean} params.order_desc - 是否降序 (可选，默认true)
 * @param {Number} params.page - 页码 (可选，默认1)
 * @param {Number} params.page_size - 每页数量 (可选，默认20)
 * @returns {Promise}
 */
export function getSkillsList(params = {}) {
  const {
    category,
    search,
    is_official,
    order_by = 'created_at',
    order_desc = true,
    page = 1,
    page_size = DEFAULT_PAGE_SIZE
  } = params

  const queryParams = {
    page,
    page_size,
    order_by,
    order_desc
  }

  // 添加可选参数
  if (category && category !== 'all') {
    queryParams.category = category
  }
  if (search) {
    queryParams.search = search
  }
  if (typeof is_official === 'boolean') {
    queryParams.is_official = is_official
  }

  return get(API_ENDPOINTS.SKILLS_LIST, queryParams, {
    loading: page === 1 // 第一页显示加载提示
  })
}

/**
 * 获取技能详情
 * @param {Number} skillId - 技能ID
 * @returns {Promise}
 */
export function getSkillDetail(skillId) {
  return get(API_ENDPOINTS.SKILL_DETAIL(skillId), {}, {
    loading: true,
    loadingText: '加载中...'
  })
}

/**
 * 分享技能（记录分享次数）
 * @param {Number} skillId - 技能ID
 * @returns {Promise}
 */
export function shareSkill(skillId) {
  return post(API_ENDPOINTS.SKILL_SHARE(skillId))
}

/**
 * 获取技能分类列表
 * @returns {Promise}
 */
export function getCategories() {
  return get(API_ENDPOINTS.SKILLS_CATEGORIES)
}

/**
 * 添加收藏
 * @param {Number} userId - 用户ID
 * @param {Number} skillId - 技能ID
 * @returns {Promise}
 */
export function addFavorite(userId, skillId) {
  return post(API_ENDPOINTS.FAVORITES_ADD, {
    user_id: userId,
    skill_id: skillId
  })
}

/**
 * 取消收藏
 * @param {Number} userId - 用户ID
 * @param {Number} skillId - 技能ID
 * @returns {Promise}
 */
export function removeFavorite(userId, skillId) {
  return del(API_ENDPOINTS.FAVORITES_REMOVE, {
    user_id: userId,
    skill_id: skillId
  })
}

/**
 * 获取用户收藏列表
 * @param {Number} userId - 用户ID
 * @param {Number} page - 页码
 * @param {Number} page_size - 每页数量
 * @returns {Promise}
 */
export function getUserFavorites(userId, page = 1, page_size = DEFAULT_PAGE_SIZE) {
  return get(API_ENDPOINTS.FAVORITES_LIST(userId), {
    page,
    page_size
  })
}

/**
 * 检查是否已收藏
 * @param {Number} userId - 用户ID
 * @param {Number} skillId - 技能ID
 * @returns {Promise}
 */
export function checkFavorite(userId, skillId) {
  return get(API_ENDPOINTS.FAVORITES_CHECK, {
    user_id: userId,
    skill_id: skillId
  })
}

export default {
  getSkillsList,
  getSkillDetail,
  shareSkill,
  getCategories,
  addFavorite,
  removeFavorite,
  getUserFavorites,
  checkFavorite
}
