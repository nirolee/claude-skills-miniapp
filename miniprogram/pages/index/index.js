// index.js
const app = getApp()

Page({
  data: {
    totalSkills: 127,
    onlineUsers: 42,
    selectedCategory: 'all',
    refreshing: false,
    loading: false,
    categories: [
      { id: 'all', name: 'All', icon: '🌐' },
      { id: 'debugging', name: 'Debugging', icon: '🐛' },
      { id: 'testing', name: 'Testing', icon: '🧪' },
      { id: 'automation', name: 'Automation', icon: '🤖' },
      { id: 'analysis', name: 'Analysis', icon: '📊' },
      { id: 'development', name: 'Development', icon: '💻' }
    ],
    skills: [
      {
        id: 1,
        name: 'webapp-testing',
        author: 'anthropics',
        authorAvatar: 'https://avatars.githubusercontent.com/u/142982089',
        category: 'debugging',
        badge: 'OFFICIAL',
        badgeType: 'cyan',
        description: 'Toolkit for interacting with and testing local web applications using Playwright',
        tags: ['playwright', 'testing', 'e2e'],
        stars: '24.5k',
        forks: '2.3k',
        downloads: '156k',
        isFavorited: false
      },
      {
        id: 2,
        name: 'systematic-debugging',
        author: 'erikpr1994',
        authorAvatar: 'https://avatars.githubusercontent.com/u/1234567',
        category: 'debugging',
        badge: 'POPULAR',
        badgeType: 'purple',
        description: 'Systematic approach to debugging complex issues with structured analysis',
        tags: ['debugging', 'analysis', 'workflow'],
        stars: '12.3k',
        forks: '890',
        downloads: '89k',
        isFavorited: false
      },
      {
        id: 3,
        name: 'code-review',
        author: 'hankhsu1996',
        authorAvatar: 'https://avatars.githubusercontent.com/u/7654321',
        category: 'analysis',
        badge: 'NEW',
        badgeType: 'green',
        description: 'Automated code review with best practices and pattern detection',
        tags: ['review', 'quality', 'patterns'],
        stars: '8.7k',
        forks: '654',
        downloads: '45k',
        isFavorited: false
      }
    ]
  },

  onLoad() {
    console.log('[Index] 页面加载')
    this.loadSkills()
    this.syncFavorites()
  },

  onShow() {
    // 每次显示页面时同步收藏状态
    this.syncFavorites()
  },

  // 同步收藏状态
  syncFavorites() {
    const skills = this.data.skills.map(skill => ({
      ...skill,
      isFavorited: app.isFavorite(skill.id)
    }))
    this.setData({ skills })
  },

  // 加载技能列表
  loadSkills() {
    // TODO: 从后端API加载技能列表
    // 目前使用Mock数据
    console.log('[Index] 技能列表加载完成')
  },

  // 选择分类
  selectCategory(e) {
    const categoryId = e.currentTarget.dataset.id
    this.setData({
      selectedCategory: categoryId
    })

    wx.showToast({
      title: `切换到 ${categoryId}`,
      icon: 'none',
      duration: 1000
    })

    // TODO: 根据分类筛选技能
  },

  // 跳转到详情页
  goToDetail(e) {
    const skillId = e.currentTarget.dataset.id
    console.log('[Index] 跳转到详情页:', skillId)

    // 添加到浏览历史
    const skill = this.data.skills.find(s => s.id === skillId)
    if (skill) {
      app.addHistory(skill)
    }

    wx.navigateTo({
      url: `/pages/detail/detail?id=${skillId}`
    })
  },

  // 切换收藏状态
  toggleFavorite(e) {
    const skillId = e.currentTarget.dataset.id
    const skills = this.data.skills.map(skill => {
      if (skill.id === skillId) {
        const newFavoriteState = !skill.isFavorited

        // 更新全局收藏列表
        if (newFavoriteState) {
          app.addFavorite(skill)
        } else {
          app.removeFavorite(skillId)
        }

        return {
          ...skill,
          isFavorited: newFavoriteState
        }
      }
      return skill
    })

    this.setData({ skills })
  },

  // 阻止事件冒泡（用于收藏按钮）
  stopPropagation() {
    // 空函数，用于阻止事件冒泡
  },

  // 下拉刷新
  onRefresh() {
    console.log('[Index] 下拉刷新')
    this.setData({ refreshing: true })

    // 模拟刷新
    setTimeout(() => {
      this.setData({ refreshing: false })
      this.loadSkills()
      this.syncFavorites()

      wx.showToast({
        title: '刷新成功',
        icon: 'success',
        duration: 1500
      })
    }, 1000)
  },

  // 加载更多
  loadMore() {
    if (this.data.loading) return

    console.log('[Index] 加载更多')
    this.setData({ loading: true })

    // TODO: 从API加载更多技能
    setTimeout(() => {
      this.setData({ loading: false })

      wx.showToast({
        title: '已加载全部',
        icon: 'none',
        duration: 1500
      })
    }, 1000)
  },

  // 滚动到顶部
  scrollToTop() {
    wx.pageScrollTo({
      scrollTop: 0,
      duration: 300
    })
  },

  // 分享
  onShareAppMessage() {
    return {
      title: 'Skill Terminal - Claude Code 技能市场',
      path: '/pages/index/index',
      imageUrl: '/static/images/share.png'
    }
  },

  // 分享到朋友圈
  onShareTimeline() {
    return {
      title: 'Skill Terminal - 发现优质 Claude Code 技能',
      query: '',
      imageUrl: '/static/images/share.png'
    }
  }
})
