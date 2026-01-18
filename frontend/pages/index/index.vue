<template>
  <view class="page">
    <!-- Terminal Header -->
    <view class="terminal-header scan-line">
      <view class="header-content">
        <view class="terminal-prompt">
          <text class="prompt-symbol">></text>
          <text class="prompt-text">claude-skills</text>
          <text class="terminal-cursor"></text>
        </view>
        <view class="header-stats">
          <view class="stat-item">
            <text class="stat-value">{{ totalSkills }}</text>
            <text class="stat-label">skills</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item">
            <text class="stat-value">{{ onlineUsers }}</text>
            <text class="stat-label">online</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Category Filter -->
    <scroll-view scroll-x class="category-scroll">
      <view class="category-container">
        <view
          v-for="(category, index) in categories"
          :key="category.id"
          :class="['category-chip', { active: selectedCategory === category.id }]"
          @click="selectCategory(category.id)"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          <text class="category-icon">{{ category.icon }}</text>
          <text class="category-name">{{ category.name }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- Skills List -->
    <scroll-view
      scroll-y
      class="skills-container"
      @scrolltolower="loadMore"
      refresher-enabled
      @refresherrefresh="onRefresh"
      :refresher-triggered="refreshing"
    >
      <view
        v-for="skill in skills"
        :key="skill.id"
        class="skill-card"
        @click="goToDetail(skill.id)"
      >
        <view class="card-glow"></view>

        <!-- Card Header -->
        <view class="card-header">
          <view class="skill-meta">
            <image :src="skill.authorAvatar" class="author-avatar" mode="aspectFill" />
            <view class="meta-info">
              <text class="author-name">{{ skill.author }}</text>
              <text class="skill-category">{{ skill.category }}</text>
            </view>
          </view>
          <view :class="['skill-badge', `badge-${skill.badgeType}`]">
            {{ skill.badge }}
          </view>
        </view>

        <!-- Skill Title -->
        <view class="skill-title-row">
          <text class="terminal-prefix">></text>
          <text class="skill-name">{{ skill.name }}</text>
        </view>

        <!-- Skill Description -->
        <text class="skill-description">{{ skill.description }}</text>

        <!-- Skill Tags -->
        <view class="skill-tags">
          <text v-for="tag in skill.tags" :key="tag" class="tag">#{{ tag }}</text>
        </view>

        <!-- Card Footer -->
        <view class="card-footer">
          <view class="stats">
            <view class="stat">
              <text class="icon-star">⭐</text>
              <text class="stat-text">{{ skill.stars }}</text>
            </view>
            <view class="stat">
              <text class="icon-fork">🔱</text>
              <text class="stat-text">{{ skill.forks }}</text>
            </view>
            <view class="stat">
              <text class="icon-download">📥</text>
              <text class="stat-text">{{ skill.downloads }}</text>
            </view>
          </view>
          <view class="action-btn" @click.stop="toggleFavorite(skill.id)">
            <text :class="['icon-heart', { favorited: skill.isFavorited }]">
              {{ skill.isFavorited ? '❤️' : '🤍' }}
            </text>
          </view>
        </view>
      </view>

      <!-- Loading State -->
      <view v-if="loading" class="loading-container">
        <view class="loading-spinner"></view>
        <text class="loading-text">加载中...</text>
      </view>

      <!-- Empty State -->
      <view v-if="!loading && skills.length === 0" class="empty-state">
        <text class="empty-icon">🔍</text>
        <text class="empty-text">暂无技能</text>
        <text class="empty-hint">下拉刷新试试</text>
      </view>
    </scroll-view>

    <!-- Floating Action Button (Back to Top) -->
    <view class="fab" @click="scrollToTop">
      <text class="fab-icon">↑</text>
      <view class="fab-glow"></view>
    </view>
  </view>
</template>

<script>
import { getSkillsList, getCategories, addFavorite, removeFavorite, checkFavorite } from '../../utils/api.js'
import { getCurrentUserId, requireLogin } from '../../utils/login.js'

export default {
  data() {
    return {
      totalSkills: 0,
      onlineUsers: 42,
      selectedCategory: 'all',
      refreshing: false,
      loading: false,
      hasMore: true,
      currentPage: 1,
      pageSize: 20,
      categories: [
        { id: 'all', name: 'All', icon: '🌐' },
      ],
      skills: [],
    }
  },
  methods: {
    /**
     * 格式化数字（如 24500 -> 24.5k）
     */
    formatNumber(num) {
      if (!num) return '0'
      if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      return num.toString()
    },

    /**
     * 加载分类列表
     */
    async loadCategories() {
      try {
        const res = await getCategories()
        if (res && res.categories) {
          // 添加 All 分类
          const allCategories = [
            { id: 'all', name: 'All', icon: '🌐' },
          ]

          // 映射分类图标
          const iconMap = {
            debugging: '🐛',
            testing: '🧪',
            automation: '🤖',
            development: '💻',
            documentation: '📝',
            design: '🎨',
            data_analysis: '📊',
            devops: '⚙️',
            other: '📦',
          }

          res.categories.forEach((cat) => {
            allCategories.push({
              id: cat.value,
              name: cat.label,
              icon: iconMap[cat.value] || '📦',
            })
          })

          this.categories = allCategories
        }
      } catch (error) {
        console.error('加载分类失败:', error)
      }
    },

    /**
     * 加载技能列表
     */
    async loadSkills(reset = false) {
      if (this.loading) return
      if (reset) {
        this.currentPage = 1
        this.skills = []
        this.hasMore = true
      }

      this.loading = true

      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize,
          order_by: 'stars',
          order_desc: true,
        }

        if (this.selectedCategory && this.selectedCategory !== 'all') {
          params.category = this.selectedCategory
        }

        const res = await getSkillsList(params)

        if (res) {
          this.totalSkills = res.total || 0

          // 转换数据格式
          const newSkills = (res.items || []).map((skill) => ({
            id: skill.id,
            name: skill.name,
            author: skill.author,
            authorAvatar: `https://avatars.githubusercontent.com/u/${skill.id}`,
            category: skill.category,
            badge: skill.is_official ? 'OFFICIAL' : (skill.stars > 50000 ? 'POPULAR' : 'NEW'),
            badgeType: skill.is_official ? 'cyan' : (skill.stars > 50000 ? 'purple' : 'green'),
            description: skill.description,
            tags: skill.tags || [],
            stars: this.formatNumber(skill.stars),
            forks: this.formatNumber(skill.forks),
            downloads: this.formatNumber(skill.view_count),
            isFavorited: false, // 稍后加载��藏状态
          }))

          if (reset) {
            this.skills = newSkills
          } else {
            this.skills = [...this.skills, ...newSkills]
          }

          // 判断是否还有更多数据
          this.hasMore = newSkills.length >= this.pageSize

          // 如果已登录，加载收藏状态
          const userId = getCurrentUserId()
          if (userId) {
            await this.loadFavoriteStatus(newSkills)
          }
        }
      } catch (error) {
        console.error('加载技能失败:', error)
        uni.showToast({
          title: '加载失败，请重试',
          icon: 'none',
        })
      } finally {
        this.loading = false
      }
    },

    /**
     * 选择分类
     */
    async selectCategory(categoryId) {
      if (this.selectedCategory === categoryId) return
      this.selectedCategory = categoryId
      await this.loadSkills(true)
    },

    /**
     * 跳转详情页
     */
    goToDetail(skillId) {
      uni.navigateTo({
        url: `/pages/detail/detail?id=${skillId}`,
      })
    },

    /**
     * 切换收藏
     */
    async toggleFavorite(skillId) {
      // 检查登录状态
      const isLoggedIn = await requireLogin()
      if (!isLoggedIn) return

      const userId = getCurrentUserId()
      const skill = this.skills.find((s) => s.id === skillId)
      if (!skill) return

      const previousState = skill.isFavorited

      try {
        // 乐观更新UI
        skill.isFavorited = !skill.isFavorited

        if (skill.isFavorited) {
          await addFavorite(userId, skillId)
          uni.showToast({
            title: '已收藏',
            icon: 'success',
          })
        } else {
          await removeFavorite(userId, skillId)
          uni.showToast({
            title: '取消收藏',
            icon: 'none',
          })
        }
      } catch (error) {
        // 回滚UI状态
        skill.isFavorited = previousState
        console.error('收藏操作失败:', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none',
        })
      }
    },

    /**
     * 加载收藏状态
     */
    async loadFavoriteStatus(skills) {
      const userId = getCurrentUserId()
      if (!userId || !skills || skills.length === 0) return

      try {
        // 批量检查收藏状态
        for (const skill of skills) {
          const res = await checkFavorite(userId, skill.id)
          skill.isFavorited = res.is_favorited || false
        }
      } catch (error) {
        console.error('加载收藏状态失败', error)
      }
    },

    /**
     * 下拉刷新
     */
    async onRefresh() {
      this.refreshing = true
      try {
        await this.loadSkills(true)
        uni.showToast({
          title: '刷新成功',
          icon: 'success',
        })
      } catch (error) {
        console.error('刷新失败:', error)
      } finally {
        this.refreshing = false
      }
    },

    /**
     * 加载更多
     */
    async loadMore() {
      if (!this.hasMore || this.loading) return
      this.currentPage++
      await this.loadSkills()
    },

    /**
     * 回到顶部
     */
    scrollToTop() {
      uni.pageScrollTo({
        scrollTop: 0,
        duration: 300,
      })
    },
  },

  /**
   * 页面加载时初始化
   */
  async mounted() {
    await this.loadCategories()
    await this.loadSkills(true)
  },
}
</script>

<style lang="scss" scoped>
/* 保留原有样式... */
.page {
  min-height: 100vh;
  background: var(--bg-primary);
  padding-bottom: 120rpx;
  overflow-x: hidden;
  width: 100%;
  position: relative;
}

/* Terminal Header */
.terminal-header {
  background: var(--bg-secondary);
  border-bottom: 2rpx solid var(--border-medium);
  padding: var(--spacing-lg) var(--spacing-md);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.terminal-prompt {
  display: flex;
  align-items: center;
  gap: 16rpx;
  font-size: 32rpx;
  font-weight: 700;
}

.prompt-symbol {
  color: var(--terminal-green);
  font-size: 36rpx;
}

.prompt-text {
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 2rpx;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--neon-cyan);
}

.stat-label {
  font-size: 20rpx;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1rpx;
}

.stat-divider {
  width: 2rpx;
  height: 32rpx;
  background: var(--border-medium);
}

/* Category Scroll */
.category-scroll {
  background: var(--bg-secondary);
  border-bottom: 1rpx solid var(--border-subtle);
  white-space: nowrap;
}

.category-container {
  display: inline-flex;
  padding: var(--spacing-md);
  gap: 16rpx;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 24rpx;
  border-radius: 48rpx;
  background: var(--bg-tertiary);
  border: 2rpx solid transparent;
  transition: all var(--transition-base);
}

.category-chip.active {
  background: rgba(0, 217, 255, 0.1);
  border-color: var(--neon-cyan);
  box-shadow: var(--shadow-glow-cyan);
}

.category-icon {
  font-size: 32rpx;
}

.category-name {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.category-chip.active .category-name {
  color: var(--neon-cyan);
}

/* Skills Container */
.skills-container {
  height: calc(100vh - 300rpx);
  padding: var(--spacing-md);
}

/* Skill Card */
.skill-card {
  position: relative;
  background: var(--bg-card);
  border: 1rpx solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  overflow: hidden;
  transition: all var(--transition-base);
}

.skill-card:active {
  transform: scale(0.98);
}

.skill-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4rpx;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple));
  opacity: 0;
  transition: opacity var(--transition-base);
}

.skill-card:active::before {
  opacity: 1;
}

.card-glow {
  position: absolute;
  inset: -2rpx;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
  opacity: 0;
  border-radius: var(--radius-lg);
  z-index: -1;
  transition: opacity var(--transition-base);
}

.skill-card:active .card-glow {
  opacity: 0.3;
}

/* Card Header */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.skill-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.author-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 2rpx solid var(--neon-cyan);
}

.meta-info {
  display: flex;
  flex-direction: column;
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

.skill-badge {
  padding: 8rpx 16rpx;
  border-radius: 24rpx;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.badge-cyan {
  background: rgba(0, 217, 255, 0.15);
  color: var(--neon-cyan);
  border: 1rpx solid var(--neon-cyan);
}

.badge-purple {
  background: rgba(168, 85, 247, 0.15);
  color: var(--neon-purple);
  border: 1rpx solid var(--neon-purple);
}

.badge-green {
  background: rgba(0, 255, 136, 0.15);
  color: var(--terminal-green);
  border: 1rpx solid var(--terminal-green);
}

/* Skill Title */
.skill-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: var(--spacing-sm);
}

.terminal-prefix {
  color: var(--terminal-green);
  font-size: 32rpx;
  font-weight: 700;
}

.skill-name {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1rpx;
}

/* Skill Description */
.skill-description {
  font-size: 26rpx;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-md);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Skill Tags */
.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: var(--spacing-md);
}

.tag {
  padding: 8rpx 16rpx;
  border-radius: 24rpx;
  background: rgba(100, 116, 139, 0.1);
  border: 1rpx solid var(--border-subtle);
  font-size: 22rpx;
  color: var(--text-tertiary);
}

/* Card Footer */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-sm);
  border-top: 1rpx solid var(--border-subtle);
}

.stats {
  display: flex;
  gap: 32rpx;
}

.stat {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.stat-text {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--text-secondary);
}

.icon-star,
.icon-fork,
.icon-download {
  font-size: 28rpx;
}

.action-btn {
  padding: 12rpx;
  border-radius: 50%;
  background: var(--bg-tertiary);
  transition: all var(--transition-base);
}

.action-btn:active {
  transform: scale(1.1);
}

.icon-heart {
  font-size: 32rpx;
  transition: all var(--transition-base);
}

/* Loading */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xl);
  gap: 16rpx;
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid var(--bg-tertiary);
  border-top-color: var(--neon-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 24rpx;
  color: var(--text-tertiary);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xl);
  gap: 16rpx;
}

.empty-icon {
  font-size: 96rpx;
  opacity: 0.3;
}

.empty-text {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-secondary);
}

.empty-hint {
  font-size: 24rpx;
  color: var(--text-tertiary);
}

/* Floating Action Button */
.fab {
  position: fixed;
  right: 32rpx;
  bottom: 160rpx;
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-glow-cyan);
  transition: all var(--transition-base);
  z-index: 99;
}

.fab:active {
  transform: scale(0.9);
}

.fab-icon {
  font-size: 40rpx;
  font-weight: 700;
  color: white;
}

.fab-glow {
  position: absolute;
  inset: -4rpx;
  border-radius: 50%;
  background: inherit;
  opacity: 0.5;
  filter: blur(8rpx);
  z-index: -1;
}
</style>
