// app.js
App({
  onLaunch() {
    // 展示本地存储能力
    const logs = wx.getStorageSync('logs') || []
    logs.unshift(Date.now())
    wx.setStorageSync('logs', logs)

    // 登录
    wx.login({
      success: res => {
        console.log('[登录] 成功:', res.code)
        // 发送 res.code 到后台换取 openId, sessionKey, unionId
      }
    })
  },

  globalData: {
    userInfo: null,
    // API Base URL (本地开发/生产环境)
    apiBaseUrl: 'http://localhost:8000/api',
    // 收藏的技能列表
    favorites: [],
    // 浏览历史
    history: []
  },

  // 添加收藏
  addFavorite(skill) {
    const favorites = wx.getStorageSync('favorites') || []
    const index = favorites.findIndex(item => item.id === skill.id)

    if (index === -1) {
      favorites.push({
        ...skill,
        favoriteTime: new Date().getTime()
      })
      wx.setStorageSync('favorites', favorites)
      this.globalData.favorites = favorites
      wx.showToast({
        title: '收藏成功',
        icon: 'success'
      })
      return true
    } else {
      wx.showToast({
        title: '已收藏',
        icon: 'none'
      })
      return false
    }
  },

  // 取消收藏
  removeFavorite(skillId) {
    let favorites = wx.getStorageSync('favorites') || []
    favorites = favorites.filter(item => item.id !== skillId)
    wx.setStorageSync('favorites', favorites)
    this.globalData.favorites = favorites
    wx.showToast({
      title: '已取消收藏',
      icon: 'success'
    })
  },

  // 检查是否已收藏
  isFavorite(skillId) {
    const favorites = wx.getStorageSync('favorites') || []
    return favorites.some(item => item.id === skillId)
  },

  // 添加浏览历史
  addHistory(skill) {
    let history = wx.getStorageSync('history') || []
    // 移除重复项
    history = history.filter(item => item.id !== skill.id)
    // 添加到开头
    history.unshift({
      ...skill,
      viewTime: new Date().getTime()
    })
    // 只保留最近50条
    if (history.length > 50) {
      history = history.slice(0, 50)
    }
    wx.setStorageSync('history', history)
    this.globalData.history = history
  },

  // 获取收藏列表
  getFavorites() {
    const favorites = wx.getStorageSync('favorites') || []
    this.globalData.favorites = favorites
    return favorites
  },

  // 获取浏览历史
  getHistory() {
    const history = wx.getStorageSync('history') || []
    this.globalData.history = history
    return history
  }
})
