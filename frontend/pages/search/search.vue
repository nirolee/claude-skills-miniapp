<template>
  <view class="search-page">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrapper">
        <text class="search-icon">🔍</text>
        <input
          class="search-input"
          type="text"
          placeholder="搜索技能名称、作者、标签..."
          v-model="searchQuery"
          @input="onSearchInput"
          @confirm="onSearchConfirm"
          confirm-type="search"
        />
        <text v-if="searchQuery" class="clear-icon" @click="clearSearch">✕</text>
      </view>
      <text v-if="searchQuery" class="cancel-btn" @click="cancelSearch">取消</text>
    </view>

    <!-- 搜索历史 -->
    <view v-if="!searchQuery && searchHistory.length > 0" class="search-history">
      <view class="history-header">
        <text class="history-title">🕐 搜索历史</text>
        <text class="clear-all-btn" @click="clearAllHistory">清空</text>
      </view>
      <view class="history-tags">
        <view
          v-for="(item, index) in searchHistory"
          :key="index"
          class="history-tag"
          @click="selectHistory(item)"
        >
          <text class="history-text">{{ item }}</text>
          <text class="delete-icon" @click.stop="deleteHistory(index)">✕</text>
        </view>
      </view>
    </view>

    <!-- 快速筛选 -->
    <view v-if="!searchQuery" class="quick-filters">
      <view class="filter-section">
        <text class="filter-title">📂 分类筛选</text>
        <view class="category-filters">
          <view
            v-for="category in categories"
            :key="category.id"
            :class="['category-item', { active: selectedCategory === category.id }]"
            @click="selectCategory(category.id)"
          >
            <text class="category-icon">{{ category.icon }}</text>
            <text class="category-name">{{ category.name }}</text>
          </view>
        </view>
      </view>

      <view class="filter-section">
        <text class="filter-title">🔥 热门标签</text>
        <view class="tag-filters">
          <text
            v-for="tag in hotTags"
            :key="tag"
            class="hot-tag"
            @click="searchByTag(tag)"
          >
            {{ tag }}
          </text>
        </view>
      </view>
    </view>

    <!-- 搜索结果 -->
    <view v-if="searchQuery" class="search-results">
      <view class="result-header">
        <text class="result-count">找到 {{ filteredSkills.length }} 个技能</text>
        <view class="sort-btn" @click="toggleSort">
          <text class="sort-icon">⇅</text>
          <text class="sort-text">{{ sortText }}</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="filteredSkills.length === 0" class="empty-state">
        <text class="empty-icon">🔍</text>
        <text class="empty-text">没有找到相关技能</text>
        <text class="empty-hint">试试其他关键词吧</text>
      </view>

      <!-- 结果列表 -->
      <view v-else class="result-list">
        <view
          v-for="skill in filteredSkills"
          :key="skill.id"
          class="skill-card"
          @click="goToDetail(skill.id)"
        >
          <view class="skill-header">
            <image class="author-avatar" :src="skill.authorAvatar" mode="aspectFill"></image>
            <view class="skill-meta">
              <text class="author-name">{{ skill.author }}</text>
              <text class="skill-category">{{ skill.category }}</text>
            </view>
            <view v-if="skill.badge" :class="['badge', `badge-${skill.badgeType}`]">
              {{ skill.badge }}
            </view>
          </view>

          <view class="skill-title">
            <text class="prompt-symbol">></text>
            <text class="skill-name">{{ highlightText(skill.name) }}</text>
          </view>

          <text class="skill-description">{{ skill.description }}</text>

          <view class="skill-footer">
            <view class="skill-stats">
              <text class="stat-text">⭐ {{ skill.stars }}</text>
              <text class="stat-text">📥 {{ skill.downloads }}</text>
            </view>
            <text :class="['favorite-icon', { favorited: skill.isFavorited }]">
              {{ skill.isFavorited ? '❤️' : '🤍' }}
            </text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getSkillsList, getCategories } from '../../utils/api.js'

export default {
  data() {
    return {
      searchQuery: '',
      searchTimer: null,
      searchHistory: [],
      selectedCategory: 'all',
      sortBy: 'stars', // stars, view_count, name
      categories: [],
      hotTags: [
        '#playwright',
        '#testing',
        '#debugging',
        '#automation',
        '#react',
        '#python',
        '#api',
        '#database',
      ],
      skills: [],
      loading: false,
      totalSkills: 0,
    }
  },
  computed: {
    filteredSkills() {
      // 已经是搜索过的结果，直接返回
      return this.skills
    },
    sortText() {
      const sortMap = {
        stars: '按星标',
        view_count: '按浏览',
        name: '按名称',
      }
      return sortMap[this.sortBy] || '排序'
    },
  },
  onLoad() {
    this.loadSearchHistory()
    this.loadCategories()
  },
  methods: {
    async loadCategories() {
      try {
        const res = await getCategories()

        // 添加 All 选项
        this.categories = [
          { id: 'all', name: 'All', icon: '🌐', count: 0 }
        ]

        // 分类图标映射
        const categoryIcons = {
          debugging: '🐛',
          testing: '🧪',
          automation: '🤖',
          analysis: '📊',
          development: '💻',
          documentation: '📚',
          deployment: '🚀',
          security: '🔒',
          general: '⚙️',
        }

        // 添加其他分类
        res.categories.forEach(cat => {
          this.categories.push({
            id: cat.category,
            name: cat.category.charAt(0).toUpperCase() + cat.category.slice(1),
            icon: categoryIcons[cat.category] || '📦',
            count: cat.count
          })
        })
      } catch (error) {
        console.error('加载分类失败', error)
      }
    },

    onSearchInput() {
      // 300ms 防抖
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => {
        if (this.searchQuery.trim()) {
          this.performSearch()
        } else {
          this.skills = []
        }
      }, 300)
    },

    onSearchConfirm() {
      if (this.searchQuery.trim()) {
        this.performSearch()
        this.addToHistory(this.searchQuery.trim())
      }
    },

    async performSearch() {
      if (this.loading) return

      try {
        this.loading = true

        const params = {
          search: this.searchQuery.trim(),
          order_by: this.sortBy === 'stars' ? 'stars' : this.sortBy === 'view_count' ? 'view_count' : 'name',
          order_desc: this.sortBy !== 'name',
          page: 1,
          page_size: 50,
        }

        // 应用分类筛选
        if (this.selectedCategory !== 'all') {
          params.category = this.selectedCategory
        }

        const res = await getSkillsList(params)

        this.totalSkills = res.total

        // 转换数据格式
        this.skills = res.items.map(skill => ({
          id: skill.id,
          name: skill.name,
          author: skill.author || 'Unknown',
          authorAvatar: `https://avatars.githubusercontent.com/u/${skill.id}?v=4`,
          category: skill.category || 'general',
          badge: skill.is_official ? 'OFFICIAL' : '',
          badgeType: skill.is_official ? 'cyan' : '',
          description: skill.description || '暂无描述',
          tags: this.parseTags(skill.tags),
          stars: this.formatNumber(skill.stars || 0),
          downloads: this.formatNumber(skill.view_count || 0),
          isFavorited: false,
        }))

        this.loading = false
      } catch (error) {
        this.loading = false
        console.error('搜索失败', error)
        uni.showToast({
          title: '搜索失败',
          icon: 'none',
        })
      }
    },

    // 解析标签
    parseTags(tags) {
      if (!tags) return []
      if (Array.isArray(tags)) return tags
      if (typeof tags === 'string') {
        try {
          const parsed = JSON.parse(tags)
          return Array.isArray(parsed) ? parsed : []
        } catch {
          return []
        }
      }
      return []
    },

    // 格式化数字
    formatNumber(num) {
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M'
      }
      if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      return num.toString()
    },

    clearSearch() {
      this.searchQuery = ''
      this.skills = []
    },

    cancelSearch() {
      this.searchQuery = ''
      this.selectedCategory = 'all'
      this.skills = []
    },

    async selectCategory(categoryId) {
      this.selectedCategory = categoryId

      // 如果有搜索词，重新搜索
      if (this.searchQuery.trim()) {
        await this.performSearch()
      }
    },

    searchByTag(tag) {
      this.searchQuery = tag.replace('#', '')
      this.performSearch()
      this.addToHistory(this.searchQuery)
    },

    toggleSort() {
      const sortOptions = ['stars', 'view_count', 'name']
      const currentIndex = sortOptions.indexOf(this.sortBy)
      this.sortBy = sortOptions[(currentIndex + 1) % sortOptions.length]

      // 重新搜索
      if (this.searchQuery.trim()) {
        this.performSearch()
      }
    },

    highlightText(text) {
      // 简单高亮，实际应该用 rich-text 组件
      return text
    },

    parseNumber(str) {
      // 解析 "24.5k" 这样的字符串为数字
      const num = parseFloat(str)
      if (str.includes('k') || str.includes('K')) return num * 1000
      if (str.includes('m') || str.includes('M')) return num * 1000000
      return num
    },

    loadSearchHistory() {
      const history = uni.getStorageSync('searchHistory')
      if (history) {
        try {
          this.searchHistory = JSON.parse(history)
        } catch {
          this.searchHistory = []
        }
      }
    },

    addToHistory(query) {
      if (!query) return
      // 去重并添加到开头
      this.searchHistory = this.searchHistory.filter((item) => item !== query)
      this.searchHistory.unshift(query)
      // 最多保留 10 条
      this.searchHistory = this.searchHistory.slice(0, 10)
      uni.setStorageSync('searchHistory', JSON.stringify(this.searchHistory))
    },

    selectHistory(query) {
      this.searchQuery = query
      this.performSearch()
    },

    deleteHistory(index) {
      this.searchHistory.splice(index, 1)
      uni.setStorageSync('searchHistory', JSON.stringify(this.searchHistory))
    },

    clearAllHistory() {
      uni.showModal({
        title: '提示',
        content: '确定清空所有搜索历史吗？',
        success: (res) => {
          if (res.confirm) {
            this.searchHistory = []
            uni.removeStorageSync('searchHistory')
          }
        },
      })
    },

    goToDetail(skillId) {
      uni.navigateTo({
        url: `/pages/detail/detail?id=${skillId}`,
      })
    },
  },
}
</script>

<style lang="scss" scoped>
.search-page {
  min-height: 100vh;
  background: var(--bg-primary);
  padding-bottom: 120rpx;
  overflow-x: hidden;
  width: 100%;
  position: relative;
}

/* 搜索栏 */
.search-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx;
  background: rgba(10, 14, 26, 0.95);
  backdrop-filter: blur(20rpx);
  border-bottom: 1rpx solid rgba(0, 217, 255, 0.1);
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16rpx;
  height: 72rpx;
  padding: 0 24rpx;
  background: rgba(0, 217, 255, 0.05);
  border: 1rpx solid rgba(0, 217, 255, 0.2);
  border-radius: 36rpx;
}

.search-icon {
  font-size: 32rpx;
  color: var(--primary-cyan);
}

.search-input {
  flex: 1;
  height: 100%;
  font-size: 28rpx;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;

  &::placeholder {
    color: var(--text-tertiary);
  }
}

.clear-icon {
  font-size: 32rpx;
  color: var(--text-tertiary);
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.cancel-btn {
  font-size: 28rpx;
  color: var(--primary-cyan);
  padding: 0 8rpx;
}

/* 搜索历史 */
.search-history {
  padding: 32rpx 24rpx;
  border-bottom: 1rpx solid var(--border-color);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.history-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.clear-all-btn {
  font-size: 24rpx;
  color: var(--text-tertiary);
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  background: rgba(255, 255, 255, 0.05);

  &:active {
    background: rgba(255, 255, 255, 0.1);
  }
}

.history-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.history-tag {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 12rpx 20rpx;
  background: rgba(0, 217, 255, 0.05);
  border: 1rpx solid rgba(0, 217, 255, 0.2);
  border-radius: 32rpx;
  transition: all 0.3s;

  &:active {
    background: rgba(0, 217, 255, 0.1);
  }
}

.history-text {
  font-size: 26rpx;
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
}

.delete-icon {
  font-size: 24rpx;
  color: var(--text-tertiary);
  width: 32rpx;
  height: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

/* 快速筛选 */
.quick-filters {
  padding: 32rpx 24rpx;
}

.filter-section {
  margin-bottom: 32rpx;

  &:last-child {
    margin-bottom: 0;
  }
}

.filter-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 24rpx;
}

.category-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 20rpx;
  background: rgba(0, 217, 255, 0.05);
  border: 1rpx solid rgba(0, 217, 255, 0.2);
  border-radius: 32rpx;
  transition: all 0.3s;

  &.active {
    background: rgba(0, 217, 255, 0.15);
    border-color: var(--primary-cyan);
  }

  &:active {
    transform: scale(0.95);
  }
}

.category-icon {
  font-size: 28rpx;
}

.category-name {
  font-size: 26rpx;
  color: var(--text-secondary);
}

.tag-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.hot-tag {
  padding: 12rpx 20rpx;
  background: rgba(168, 85, 247, 0.1);
  border: 1rpx solid rgba(168, 85, 247, 0.3);
  border-radius: 32rpx;
  font-size: 26rpx;
  color: var(--primary-purple);
  font-family: 'Courier New', monospace;
  transition: all 0.3s;

  &:active {
    background: rgba(168, 85, 247, 0.2);
    transform: scale(0.95);
  }
}

/* 搜索结果 */
.search-results {
  padding: 24rpx;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.result-count {
  font-size: 28rpx;
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
}

.sort-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 16rpx;
  background: rgba(0, 217, 255, 0.1);
  border-radius: 8rpx;
  border: 1rpx solid rgba(0, 217, 255, 0.2);

  &:active {
    background: rgba(0, 217, 255, 0.2);
  }
}

.sort-icon {
  font-size: 24rpx;
  color: var(--primary-cyan);
}

.sort-text {
  font-size: 24rpx;
  color: var(--primary-cyan);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 48rpx;
}

.empty-icon {
  font-size: 128rpx;
  margin-bottom: 32rpx;
}

.empty-text {
  font-size: 32rpx;
  color: var(--text-secondary);
  margin-bottom: 16rpx;
}

.empty-hint {
  font-size: 24rpx;
  color: var(--text-tertiary);
}

/* 结果列表 */
.result-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.skill-card {
  padding: 24rpx;
  background: rgba(0, 217, 255, 0.03);
  border: 1rpx solid rgba(0, 217, 255, 0.1);
  border-radius: 16rpx;
  transition: all 0.3s;

  &:active {
    background: rgba(0, 217, 255, 0.05);
    transform: scale(0.98);
  }
}

.skill-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.author-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 2rpx solid var(--primary-cyan);
}

.skill-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.author-name {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.skill-category {
  font-size: 20rpx;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.badge {
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  font-size: 20rpx;
  font-weight: 600;

  &.badge-cyan {
    background: rgba(0, 217, 255, 0.15);
    color: var(--primary-cyan);
  }

  &.badge-purple {
    background: rgba(168, 85, 247, 0.15);
    color: var(--primary-purple);
  }

  &.badge-green {
    background: rgba(0, 255, 136, 0.15);
    color: var(--terminal-green);
  }
}

.skill-title {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 12rpx;
}

.prompt-symbol {
  font-size: 28rpx;
  color: var(--terminal-green);
  font-family: 'Courier New', monospace;
}

.skill-name {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

.skill-description {
  display: block;
  font-size: 26rpx;
  line-height: 1.5;
  color: var(--text-secondary);
  margin-bottom: 16rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.skill-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.skill-stats {
  display: flex;
  gap: 24rpx;
}

.stat-text {
  font-size: 22rpx;
  color: var(--text-tertiary);
  font-family: 'Courier New', monospace;
}

.favorite-icon {
  font-size: 32rpx;

  &.favorited {
    animation: heartBeat 0.3s ease;
  }
}

@keyframes heartBeat {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}
</style>
