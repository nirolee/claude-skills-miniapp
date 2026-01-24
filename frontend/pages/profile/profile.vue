<template>
  <view class="profile-page">
    <!-- 用户信息区域 -->
    <view class="user-section">
      <view class="user-card" v-if="isLoggedIn">
        <button class="avatar-wrapper" open-type="chooseAvatar" @chooseavatar="onChooseAvatar">
          <image class="user-avatar" :src="userInfo.avatar_url || defaultAvatar" mode="aspectFill"></image>
        </button>
        <view class="user-info">
          <input
            class="user-name-input"
            type="nickname"
            :value="userInfo.nickname || '点击设置昵称'"
            @blur="onNicknameBlur"
            placeholder="点击设置昵称"
          />
        </view>
      </view>

      <view class="login-card" v-else @click="handleLogin">
        <text class="login-icon">⚡</text>
        <text class="login-text">点击登录</text>
        <text class="login-hint">快速登录后设置头像昵称</text>
      </view>
    </view>

    <!-- 收藏列表 -->
    <view class="favorites-section" v-if="isLoggedIn">
      <view class="section-header">
        <text class="section-title">我的收藏</text>
        <text class="section-count">{{ totalFavorites }}</text>
      </view>

      <view class="favorites-list" v-if="favoriteSkills.length > 0">
        <view
          class="skill-item"
          v-for="skill in favoriteSkills"
          :key="skill.id"
          @click="goToDetail(skill.id)"
        >
          <view class="skill-header">
            <text class="skill-name">{{ skill.name }}</text>
            <text class="skill-category">{{ skill.category }}</text>
          </view>
          <text class="skill-description">{{ skill.description }}</text>
          <view class="skill-meta">
            <text class="meta-item">⭐ {{ skill.stars }}</text>
            <text class="meta-item">👁️ {{ skill.view_count }}</text>
            <text class="meta-item">{{ formatDate(skill.created_at) }}</text>
          </view>
        </view>
      </view>

      <view class="empty-state" v-else>
        <text class="empty-icon">📦</text>
        <text class="empty-text">暂无收藏</text>
        <view class="empty-button" @click="goToHome">
          <text class="empty-button-text">去浏览技能</text>
        </view>
      </view>

      <!-- 加载更多 -->
      <view class="load-more" v-if="favoriteSkills.length > 0 && hasMore">
        <text class="load-more-text" @click="loadMoreFavorites">加载更多</text>
      </view>
    </view>

    <!-- 设置区域 -->
    <view class="settings-section">
      <view class="section-header">
        <text class="section-title">设置</text>
      </view>

      <view class="settings-list">
        <view class="setting-item" @click="goToPrivacy">
          <text class="setting-label">隐私政策</text>
          <text class="setting-arrow">→</text>
        </view>
        <view class="setting-item" @click="clearCache">
          <text class="setting-label">清除缓存</text>
          <text class="setting-arrow">→</text>
        </view>
        <view class="setting-item" @click="goToAbout">
          <text class="setting-label">关于我们</text>
          <text class="setting-arrow">→</text>
        </view>
        <view class="setting-item" v-if="isLoggedIn" @click="handleLogout">
          <text class="setting-label logout">退出登录</text>
          <text class="setting-arrow">→</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { wxLogin, checkLogin, getCurrentUser, getCurrentUserId, logout } from '../../utils/login.js'
import { getUserFavorites, updateUserProfile } from '../../utils/api.js'
import { getCurrentLanguage, updateTabBarLanguage } from '../../utils/language.js'

export default {
  data() {
    return {
      isLoggedIn: false,
      userInfo: null,
      favoriteSkills: [],
      totalFavorites: 0,
      currentPage: 1,
      pageSize: 20,
      hasMore: true,
      loading: false,
      defaultAvatar: 'https://avatars.githubusercontent.com/u/1?v=4'
    }
  },

  onShow() {
    // 更新 TabBar 语言
    updateTabBarLanguage(getCurrentLanguage())

    this.checkLoginStatus()
    if (this.isLoggedIn) {
      this.loadFavorites()
    }
  },

  methods: {
    // 检查登录状态
    checkLoginStatus() {
      this.isLoggedIn = checkLogin()
      if (this.isLoggedIn) {
        this.userInfo = getCurrentUser()
      }
    },

    // 选择头像
    async onChooseAvatar(e) {
      const { avatarUrl } = e.detail
      try {
        // 调用后端API更新头像
        const res = await updateUserProfile(this.userInfo.user_id, {
          avatar_url: avatarUrl
        })

        // 更新本地用户信息
        this.userInfo.avatar_url = avatarUrl
        uni.setStorageSync('user', this.userInfo)

        uni.showToast({
          title: '头像已更新',
          icon: 'success'
        })
      } catch (error) {
        console.error('更新头像失败', error)
        uni.showToast({
          title: '更新失败',
          icon: 'none'
        })
      }
    },

    // 昵称输入框失焦
    async onNicknameBlur(e) {
      const nickname = e.detail.value.trim()
      if (!nickname || nickname === this.userInfo.nickname) {
        return
      }

      try {
        // 调用后端API更新昵称
        const res = await updateUserProfile(this.userInfo.user_id, {
          nickname
        })

        // 更新本地用户信息
        this.userInfo.nickname = nickname
        uni.setStorageSync('user', this.userInfo)

        uni.showToast({
          title: '昵称已更新',
          icon: 'success'
        })
      } catch (error) {
        console.error('更新昵称失败', error)
        uni.showToast({
          title: '更新失败',
          icon: 'none'
        })
      }
    },

    // 处理登录
    async handleLogin() {
      try {
        uni.showLoading({ title: '登录中...' })
        const user = await wxLogin()
        this.isLoggedIn = true
        this.userInfo = user

        uni.hideLoading()
        uni.showToast({
          title: user.is_new_user ? '欢迎新用户！' : '登录成功',
          icon: 'success'
        })

        // 加载收藏列表
        this.loadFavorites()
      } catch (error) {
        uni.hideLoading()
        console.error('登录失败', error)
      }
    },

    // 处理退出登录
    handleLogout() {
      uni.showModal({
        title: '提示',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            logout()
            this.isLoggedIn = false
            this.userInfo = null
            this.favoriteSkills = []
            this.totalFavorites = 0
          }
        }
      })
    },

    // 加载收藏列表
    async loadFavorites(reset = false) {
      if (this.loading) return
      if (!this.isLoggedIn) return

      if (reset) {
        this.currentPage = 1
        this.favoriteSkills = []
        this.hasMore = true
      }

      try {
        this.loading = true
        const userId = getCurrentUserId()

        const res = await getUserFavorites(userId, this.currentPage, this.pageSize)

        console.log('收藏列表 API 响应:', res)

        this.totalFavorites = res.total

        // 确保数据格式正确
        const formattedItems = (res.items || []).map(item => ({
          id: item.skill_id,
          name: item.name || item.skill_name || '未命名技能',
          description: item.description || item.skill_description || '暂无描述',
          category: item.category || item.skill_category || 'general',
          stars: item.stars || item.skill_stars || 0,
          view_count: item.view_count || 0,
          created_at: item.created_at
        }))

        console.log('格式化后的收藏列表:', formattedItems)

        if (this.currentPage === 1) {
          this.favoriteSkills = formattedItems
        } else {
          this.favoriteSkills = [...this.favoriteSkills, ...formattedItems]
        }

        // 判断是否还有更多数据
        this.hasMore = this.favoriteSkills.length < res.total

        this.loading = false
      } catch (error) {
        this.loading = false
        console.error('加载收藏失败', error)
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        })
      }
    },

    // 加载更多收藏
    async loadMoreFavorites() {
      if (!this.hasMore || this.loading) return

      this.currentPage++
      await this.loadFavorites()
    },

    // 跳转到技能详情
    goToDetail(skillId) {
      uni.navigateTo({
        url: `/pages/detail/detail?id=${skillId}`
      })
    },

    // 跳转到首页
    goToHome() {
      uni.switchTab({
        url: '/pages/index/index'
      })
    },

    // 清除缓存
    clearCache() {
      uni.showModal({
        title: '提示',
        content: '确定要清除缓存吗？',
        success: (res) => {
          if (res.confirm) {
            try {
              // 只清除非登录相关的缓存
              const keysToKeep = ['user', 'token', 'user_id']
              const allKeys = uni.getStorageInfoSync().keys

              allKeys.forEach(key => {
                if (!keysToKeep.includes(key)) {
                  uni.removeStorageSync(key)
                }
              })

              uni.showToast({
                title: '清除成功',
                icon: 'success'
              })
            } catch (error) {
              uni.showToast({
                title: '清除失败',
                icon: 'none'
              })
            }
          }
        }
      })
    },

    // 跳转到关于页面
    goToAbout() {
      uni.showModal({
        title: 'Claude Skills',
        content: 'Claude Code 技能市场小程序\n版本：1.0.0\n\n发现、收藏和安装优质 Claude Code 技能',
        showCancel: false
      })
    },

    // 跳转到隐私政策
    goToPrivacy() {
      uni.navigateTo({
        url: '/pages/privacy/privacy'
      })
    },

    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date

      // 小于1天
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000)
        return hours < 1 ? '刚刚' : `${hours}小时前`
      }

      // 小于7天
      if (diff < 604800000) {
        const days = Math.floor(diff / 86400000)
        return `${days}天前`
      }

      // 显示日期
      return `${date.getMonth() + 1}/${date.getDate()}`
    },

    /**
     * 分享给朋友
     */
    onShareAppMessage() {
      return {
        title: 'Claude Skills - 技能市场',
        path: '/pages/index/index',
        imageUrl: '',
      }
    },

    /**
     * 分享到朋友圈
     */
    onShareTimeline() {
      return {
        title: 'Claude Skills - 发现优质 Claude Code 技能',
        query: '',
        imageUrl: '',
      }
    },
  }
}
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: var(--bg-primary);
  padding-bottom: calc(env(safe-area-inset-bottom) + 120rpx);
  overflow-x: hidden;
  width: 100%;
  position: relative;
}

/* 用户信息区域 */
.user-section {
  padding: 60rpx 40rpx;
  background: linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(168, 85, 247, 0.05) 100%);
  border-bottom: 2rpx solid var(--border-color);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 32rpx;
  padding: 40rpx;
  background: var(--bg-secondary);
  border: 2rpx solid var(--primary-color);
  border-radius: 16rpx;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4rpx;
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color), var(--success-color));
  }
}

.avatar-wrapper {
  padding: 0;
  margin: 0;
  background: transparent;
  border: none;
  line-height: 1;

  &::after {
    border: none;
  }
}

.user-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  border: 4rpx solid var(--primary-color);
  background: var(--bg-primary);
  display: block;
  cursor: pointer;
  transition: all 0.3s;

  &:active {
    transform: scale(0.95);
    border-color: var(--accent-color);
  }
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.user-name {
  font-size: 36rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.user-name-input {
  font-size: 36rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
  padding: 0;
  background: transparent;
  border: none;
  outline: none;
  width: 100%;

  &::placeholder {
    color: var(--text-tertiary);
    opacity: 0.6;
  }
}

.user-id {
  font-size: 24rpx;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}

.terminal-cursor {
  font-size: 32rpx;
  color: var(--success-color);
  animation: blink 1s infinite;
}

.login-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24rpx;
  padding: 80rpx 40rpx;
  background: var(--bg-secondary);
  border: 2rpx dashed var(--primary-color);
  border-radius: 16rpx;
  cursor: pointer;
  transition: all 0.3s;

  &:active {
    transform: scale(0.98);
    border-color: var(--accent-color);
  }
}

.login-icon {
  font-size: 64rpx;
}

.login-text {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.login-hint {
  font-size: 24rpx;
  color: var(--text-tertiary);
}

/* 收藏列表区域 */
.favorites-section {
  padding: 40rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32rpx;
  padding-bottom: 16rpx;
  border-bottom: 2rpx solid var(--border-color);
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);

  &::before {
    content: '> ';
    color: var(--primary-color);
  }
}

.section-count {
  font-size: 24rpx;
  color: var(--text-secondary);
  padding: 8rpx 16rpx;
  background: var(--bg-secondary);
  border: 1rpx solid var(--primary-color);
  border-radius: 8rpx;
  font-family: var(--font-mono);
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.skill-item {
  padding: 32rpx;
  background: var(--bg-secondary);
  border: 2rpx solid var(--border-color);
  border-radius: 12rpx;
  transition: all 0.3s;

  &:active {
    border-color: var(--primary-color);
    transform: translateX(8rpx);
  }
}

.skill-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.skill-name {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-category {
  font-size: 20rpx;
  color: var(--primary-color);
  padding: 4rpx 12rpx;
  background: rgba(0, 217, 255, 0.1);
  border: 1rpx solid var(--primary-color);
  border-radius: 8rpx;
  margin-left: 16rpx;
}

.skill-description {
  font-size: 24rpx;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-meta {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.meta-item {
  font-size: 22rpx;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24rpx;
  padding: 120rpx 40rpx;
}

.empty-icon {
  font-size: 96rpx;
  opacity: 0.5;
}

.empty-text {
  font-size: 28rpx;
  color: var(--text-tertiary);
}

.empty-button {
  margin-top: 24rpx;
  padding: 16rpx 48rpx;
  background: var(--primary-color);
  border-radius: 8rpx;
  cursor: pointer;
  transition: all 0.3s;

  &:active {
    transform: scale(0.95);
    opacity: 0.8;
  }
}

.empty-button-text {
  font-size: 26rpx;
  color: var(--bg-primary);
  font-weight: 600;
}

/* 加载更多 */
.load-more {
  display: flex;
  justify-content: center;
  padding: 32rpx 0;
  margin-top: 24rpx;
}

.load-more-text {
  font-size: 26rpx;
  color: var(--primary-color);
  padding: 16rpx 48rpx;
  border: 2rpx solid var(--primary-color);
  border-radius: 8rpx;
  cursor: pointer;
  transition: all 0.3s;

  &:active {
    background: var(--primary-color);
    color: var(--bg-primary);
  }
}

/* 设置区域 */
.settings-section {
  padding: 40rpx;
}

.settings-list {
  display: flex;
  flex-direction: column;
  gap: 2rpx;
  background: var(--bg-secondary);
  border: 2rpx solid var(--border-color);
  border-radius: 12rpx;
  overflow: hidden;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  background: var(--bg-secondary);
  transition: all 0.3s;
  cursor: pointer;

  &:not(:last-child) {
    border-bottom: 1rpx solid var(--border-color);
  }

  &:active {
    background: rgba(0, 217, 255, 0.05);
  }
}

.setting-label {
  font-size: 28rpx;
  color: var(--text-primary);
  font-family: var(--font-mono);

  &.logout {
    color: var(--error-color);
  }
}

.setting-arrow {
  font-size: 28rpx;
  color: var(--text-tertiary);
}

@keyframes blink {
  0%, 49% {
    opacity: 1;
  }
  50%, 100% {
    opacity: 0;
  }
}
</style>
