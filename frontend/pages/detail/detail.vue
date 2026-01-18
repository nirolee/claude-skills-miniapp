<template>
  <view class="detail-page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="nav-icon">←</text>
      </view>
      <view class="nav-title">{{ skill.name || '技能详情' }}</view>
      <view class="nav-share" @click="onShare">
        <text class="nav-icon">⤴</text>
      </view>
    </view>

    <!-- 技能头部信息 -->
    <view class="skill-header">
      <view class="author-info">
        <image class="author-avatar" :src="skill.authorAvatar" mode="aspectFill"></image>
        <view class="author-meta">
          <text class="author-name">{{ skill.author }}</text>
          <text class="skill-category">{{ skill.category }}</text>
        </view>
        <view v-if="skill.badge" :class="['badge', `badge-${skill.badgeType}`]">
          {{ skill.badge }}
        </view>
      </view>

      <view class="skill-title">
        <text class="prompt-symbol">></text>
        <text class="skill-name">{{ skill.name }}</text>
      </view>

      <text class="skill-description">{{ skill.description }}</text>

      <!-- GitHub 统计 -->
      <view class="skill-stats">
        <view class="stat-item">
          <text class="stat-icon">⭐</text>
          <text class="stat-value">{{ skill.stars }}</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">🔱</text>
          <text class="stat-value">{{ skill.forks }}</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">📥</text>
          <text class="stat-value">{{ skill.downloads }}</text>
        </view>
        <view class="favorite-btn" @click="toggleFavorite">
          <text class="favorite-icon">{{ skill.isFavorited ? '❤️' : '🤍' }}</text>
        </view>
      </view>
    </view>

    <!-- 标签区域 -->
    <view class="tags-section" v-if="skill.tags && skill.tags.length > 0">
      <text v-for="tag in skill.tags" :key="tag" class="tag">{{ tag }}</text>
    </view>

    <!-- 安装命令区域 -->
    <view class="install-section">
      <view class="section-header">
        <text class="section-icon">📦</text>
        <text class="section-title">安装命令</text>
      </view>
      <view class="install-command" @click="copyCommand">
        <text class="command-text">{{ skill.installCommand }}</text>
        <text class="copy-icon">📋</text>
      </view>
      <text class="install-hint">点击复制安装命令</text>
    </view>

    <!-- Markdown 内容区域 -->
    <view class="content-section">
      <view class="section-header">
        <text class="section-icon">📄</text>
        <text class="section-title">详细说明</text>
      </view>
      <view class="markdown-content">
        <text class="markdown-text">{{ skill.content || '暂无详细说明，请访问 GitHub 仓库查看完整文档。' }}</text>
      </view>
    </view>

    <!-- 相关推荐 -->
    <view class="related-section">
      <view class="section-header">
        <text class="section-icon">🔗</text>
        <text class="section-title">相关推荐</text>
      </view>
      <view class="related-list">
        <view
          v-for="item in relatedSkills"
          :key="item.id"
          class="related-item"
          @click="goToSkill(item.id)"
        >
          <image class="related-avatar" :src="item.authorAvatar" mode="aspectFill"></image>
          <view class="related-info">
            <text class="related-name">> {{ item.name }}</text>
            <text class="related-desc">{{ item.description }}</text>
          </view>
          <text class="related-arrow">→</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getSkillDetail, shareSkill, addFavorite, removeFavorite, checkFavorite, getSkillsList } from '../../utils/api.js'
import { requireLogin, getCurrentUserId } from '../../utils/login.js'

export default {
  data() {
    return {
      skillId: null,
      skill: {
        id: null,
        name: '',
        author: '',
        authorAvatar: '',
        category: '',
        badge: '',
        badgeType: '',
        description: '',
        tags: [],
        stars: '0',
        forks: '0',
        downloads: '0',
        isFavorited: false,
        installCommand: '',
        content: '',
      },
      relatedSkills: [],
      loading: false,
    }
  },
  onLoad(options) {
    if (options.id) {
      this.skillId = parseInt(options.id)
      this.loadSkill(this.skillId)
    }
  },
  methods: {
    async loadSkill(id) {
      if (this.loading) return

      try {
        this.loading = true

        // 加载技能详情
        const skillData = await getSkillDetail(id)

        // 转换数据格式
        this.skill = {
          id: skillData.id,
          name: skillData.name,
          author: skillData.author || 'Unknown',
          authorAvatar: `https://avatars.githubusercontent.com/u/${skillData.id}?v=4`,
          category: skillData.category || 'general',
          badge: skillData.is_official ? 'OFFICIAL' : '',
          badgeType: skillData.is_official ? 'cyan' : '',
          description: skillData.description || '暂无描述',
          tags: this.parseTags(skillData.tags),
          stars: this.formatNumber(skillData.stars || 0),
          forks: this.formatNumber(skillData.forks || 0),
          downloads: this.formatNumber(skillData.view_count || 0),
          isFavorited: false,
          installCommand: skillData.install_command || `claude skill install ${skillData.github_url}`,
          content: skillData.content || '暂无详细说明，请访问 GitHub 仓库查看完整文档。',
        }

        // 检查是否已收藏
        await this.checkFavoriteStatus()

        // 加载相关推荐
        await this.loadRelatedSkills(skillData.category)

        this.loading = false
      } catch (error) {
        this.loading = false
        console.error('加载技能详情失败', error)
        uni.showToast({
          title: '加载失败',
          icon: 'none',
        })
      }
    },

    // 检查收藏状态
    async checkFavoriteStatus() {
      const userId = getCurrentUserId()
      if (!userId) {
        this.skill.isFavorited = false
        return
      }

      try {
        const res = await checkFavorite(userId, this.skill.id)
        this.skill.isFavorited = res.is_favorited || false
      } catch (error) {
        console.error('检查收藏状态失败', error)
        this.skill.isFavorited = false
      }
    },

    // 加载相关推荐
    async loadRelatedSkills(category) {
      try {
        const res = await getSkillsList({
          category: category,
          page: 1,
          page_size: 3,
        })

        this.relatedSkills = res.items
          .filter(item => item.id !== this.skill.id)
          .slice(0, 2)
          .map(item => ({
            id: item.id,
            name: item.name,
            author: item.author || 'Unknown',
            authorAvatar: `https://avatars.githubusercontent.com/u/${item.id}?v=4`,
            description: item.description || '暂无描述',
          }))
      } catch (error) {
        console.error('加载相关推荐失败', error)
        this.relatedSkills = []
      }
    },

    // 解析标签
    parseTags(tags) {
      if (!tags) return []
      if (Array.isArray(tags)) return tags.map(t => `#${t}`)
      if (typeof tags === 'string') {
        try {
          const parsed = JSON.parse(tags)
          return Array.isArray(parsed) ? parsed.map(t => `#${t}`) : []
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

    goBack() {
      uni.navigateBack()
    },

    async onShare() {
      try {
        // 记录分享次数
        await shareSkill(this.skill.id)

        uni.showToast({
          title: '感谢分享',
          icon: 'success',
        })
      } catch (error) {
        console.error('分享失败', error)
      }
    },

    async toggleFavorite() {
      // 检查登录状态
      const isLoggedIn = await requireLogin()
      if (!isLoggedIn) return

      const userId = getCurrentUserId()
      const previousState = this.skill.isFavorited

      try {
        // 乐观更新 UI
        this.skill.isFavorited = !this.skill.isFavorited

        if (this.skill.isFavorited) {
          await addFavorite(userId, this.skill.id)
          uni.showToast({
            title: '已收藏',
            icon: 'success',
          })
        } else {
          await removeFavorite(userId, this.skill.id)
          uni.showToast({
            title: '取消收藏',
            icon: 'success',
          })
        }
      } catch (error) {
        // 回滚 UI 状态
        this.skill.isFavorited = previousState
        console.error('收藏操作失败', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none',
        })
      }
    },

    copyCommand() {
      uni.setClipboardData({
        data: this.skill.installCommand,
        success: () => {
          uni.showToast({
            title: '已复制到剪贴板',
            icon: 'success',
          })
        },
      })
    },

    goToSkill(id) {
      uni.redirectTo({
        url: `/pages/detail/detail?id=${id}`,
      })
    },
  },
}
</script>

<style lang="scss" scoped>
.detail-page {
  min-height: 100vh;
  background: var(--bg-primary);
  padding-bottom: 40rpx;
  overflow-x: hidden;
  width: 100%;
  position: relative;
}

/* 自定义导航栏 */
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 24rpx;
  background: rgba(10, 14, 26, 0.95);
  backdrop-filter: blur(20rpx);
  border-bottom: 1rpx solid rgba(0, 217, 255, 0.1);
}

.nav-back,
.nav-share {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 217, 255, 0.1);
  transition: all 0.3s;

  &:active {
    background: rgba(0, 217, 255, 0.2);
    transform: scale(0.95);
  }
}

.nav-icon {
  font-size: 36rpx;
  color: var(--primary-cyan);
}

.nav-title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

/* 技能头部信息 */
.skill-header {
  padding: 32rpx 24rpx;
  border-bottom: 1rpx solid var(--border-color);
}

.author-info {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.author-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  border: 2rpx solid var(--primary-cyan);
}

.author-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.author-name {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.skill-category {
  font-size: 22rpx;
  color: var(--text-secondary);
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
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.prompt-symbol {
  font-size: 32rpx;
  color: var(--terminal-green);
  font-family: 'Courier New', monospace;
}

.skill-name {
  font-size: 40rpx;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

.skill-description {
  display: block;
  font-size: 28rpx;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 24rpx;
}

.skill-stats {
  display: flex;
  align-items: center;
  gap: 32rpx;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.stat-icon {
  font-size: 28rpx;
}

.stat-value {
  font-size: 24rpx;
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
}

.favorite-btn {
  margin-left: auto;
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 217, 255, 0.1);
  transition: all 0.3s;

  &:active {
    background: rgba(0, 217, 255, 0.2);
    transform: scale(0.95);
  }
}

.favorite-icon {
  font-size: 40rpx;
}

/* 标签区域 */
.tags-section {
  padding: 24rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  border-bottom: 1rpx solid var(--border-color);
}

.tag {
  padding: 8rpx 16rpx;
  background: rgba(0, 217, 255, 0.1);
  border-radius: 8rpx;
  font-size: 24rpx;
  color: var(--primary-cyan);
  font-family: 'Courier New', monospace;
}

/* 通用 Section 样式 */
.install-section,
.content-section,
.related-section {
  padding: 32rpx 24rpx;
  border-bottom: 1rpx solid var(--border-color);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.section-icon {
  font-size: 32rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
}

/* 安装命令区域 */
.install-command {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx;
  background: rgba(0, 217, 255, 0.15);
  border: 2rpx solid rgba(0, 217, 255, 0.5);
  border-radius: 16rpx;
  margin-bottom: 12rpx;
  transition: all 0.3s;
  box-shadow: 0 0 20rpx rgba(0, 217, 255, 0.15);

  &:active {
    background: rgba(0, 217, 255, 0.25);
    border-color: var(--neon-cyan);
    box-shadow: 0 0 30rpx rgba(0, 217, 255, 0.3);
    transform: scale(0.98);
  }
}

.command-text {
  flex: 1;
  font-size: 24rpx;
  color: var(--neon-cyan);
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

.copy-icon {
  font-size: 32rpx;
}

.install-hint {
  display: block;
  font-size: 22rpx;
  color: var(--text-tertiary);
  text-align: center;
}

/* Markdown 内容区域 */
.markdown-content {
  padding: 24rpx;
  background: rgba(0, 217, 255, 0.03);
  border-radius: 16rpx;
  border: 1rpx solid rgba(0, 217, 255, 0.1);
}

.markdown-text {
  font-size: 28rpx;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

/* 相关推荐 */
.related-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.related-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx;
  background: rgba(0, 217, 255, 0.05);
  border-radius: 16rpx;
  border: 1rpx solid rgba(0, 217, 255, 0.1);
  transition: all 0.3s;

  &:active {
    background: rgba(0, 217, 255, 0.1);
    transform: scale(0.98);
  }
}

.related-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  border: 2rpx solid var(--primary-cyan);
}

.related-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.related-name {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

.related-desc {
  font-size: 24rpx;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.related-arrow {
  font-size: 32rpx;
  color: var(--primary-cyan);
}
</style>
