<template>
  <view class="privacy-page">
    <view class="privacy-header">
      <text class="privacy-title">隐私保护指引</text>
      <text class="update-time">更新日期：2026年1月24日</text>
      <text class="effective-time">生效日期：2026年1月24日</text>
    </view>

    <scroll-view scroll-y class="privacy-content">
      <view class="section">
        <text class="section-title">一、引言</text>
        <text class="section-text">
          skill技能助手（以下简称"本小程序"）深知个人信息对您的重要性，我们将按照法律法规要求，采取相应安全保护措施，尽力保护您的个人信息安全可控。
        </text>
      </view>

      <view class="section">
        <text class="section-title">二、我们如何收集和使用您的个人信息</text>

        <text class="sub-title">1. 用户头像和昵称</text>
        <text class="section-text">
          当您使用个人中心功能时，我们会请求您授权获取您的头像和昵称信息，用于：
        </text>
        <text class="list-item">• 展示您的个人资料</text>
        <text class="list-item">• 识别您的账户身份</text>
        <text class="list-item">• 提供个性化服务</text>
        <text class="section-text">
          您可以选择不提供这些信息，但可能无法使用部分功能。
        </text>

        <text class="sub-title">2. 收藏和浏览记录</text>
        <text class="section-text">
          当您浏览技能、收藏技能时，我们会收集：
        </text>
        <text class="list-item">• 浏览的技能信息</text>
        <text class="list-item">• 收藏的技能列表</text>
        <text class="list-item">• 搜索历史记录</text>
        <text class="section-text">
          这些信息用于为您提供更好的推荐服务和个性化体验。
        </text>
      </view>

      <view class="section">
        <text class="section-title">三、我们如何存储和保护您的个人信息</text>
        <text class="section-text">
          1. 我们采用业界标准的安全技术措施保护您的个人信息安全；
        </text>
        <text class="section-text">
          2. 您的个人信息存储在安全的服务器中，我们会采取加密等措施保护数据安全；
        </text>
        <text class="section-text">
          3. 我们会采取合理可行的措施，尽力避免收集无关的个人信息。
        </text>
      </view>

      <view class="section">
        <text class="section-title">四、我们如何使用 Cookie 和同类技术</text>
        <text class="section-text">
          我们使用本地存储技术（如 localStorage）来保存您的：
        </text>
        <text class="list-item">• 登录状态</text>
        <text class="list-item">• 语言偏好设置</text>
        <text class="list-item">• 搜索历史记录</text>
        <text class="section-text">
          您可以在个人中心-设置中清除缓存数据。
        </text>
      </view>

      <view class="section">
        <text class="section-title">五、我们如何共享、转让、公开披露您的个人信息</text>
        <text class="section-text">
          我们不会与任何第三方共享、转让或公开披露您的个人信息，除非：
        </text>
        <text class="list-item">• 获得您的明确同意</text>
        <text class="list-item">• 法律法规规定的情况</text>
        <text class="list-item">• 与关联公司共享（需符合本政策约定）</text>
      </view>

      <view class="section">
        <text class="section-title">六、您的权利</text>
        <text class="section-text">
          您对自己的个人信息享有以下权利：
        </text>
        <text class="list-item">• 访问您的个人信息</text>
        <text class="list-item">• 更正您的个人信息</text>
        <text class="list-item">• 删除您的个人信息</text>
        <text class="list-item">• 撤回已同意的授权</text>
        <text class="list-item">• 注销您的账户</text>
      </view>

      <view class="section">
        <text class="section-title">七、未成年人保护</text>
        <text class="section-text">
          我们重视未成年人的个人信息保护。如您为未成年人，请在监护人的陪同下阅读本政策，并在监护人同意的前提下使用我们的服务。
        </text>
      </view>

      <view class="section">
        <text class="section-title">八、本政策如何更新</text>
        <text class="section-text">
          我们可能适时修订本政策内容。如该等变更会导致您在本政策项下权利的实质减损，我们将在变更生效前，通过页面提示、弹窗等方式通知您。
        </text>
      </view>

      <view class="section">
        <text class="section-title">九、如何联系我们</text>
        <text class="section-text">
          如您对本隐私政策有任何疑问、意见或建议，可通过以下方式联系我们：
        </text>
        <text class="list-item">• 邮箱：nirolee@foxmail.com</text>
        <text class="section-text">
          我们将在15个工作日内回复您的请求。
        </text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
export default {
  data() {
    return {}
  },
  methods: {}
}
</script>

<style lang="scss" scoped>
.privacy-page {
  min-height: 100vh;
  background: var(--bg-primary);
  padding-bottom: 40rpx;
}

.privacy-header {
  padding: 60rpx 40rpx 40rpx;
  background: linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(168, 85, 247, 0.05) 100%);
  border-bottom: 2rpx solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.privacy-title {
  font-size: 48rpx;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.update-time,
.effective-time {
  font-size: 24rpx;
  color: var(--text-tertiary);
}

.privacy-content {
  height: calc(100vh - 240rpx);
  padding: 40rpx;
}

.section {
  margin-bottom: 48rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  padding-bottom: 16rpx;
  border-bottom: 2rpx solid var(--primary-color);
  font-family: var(--font-mono);
}

.sub-title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-secondary);
  margin-top: 20rpx;
}

.section-text {
  font-size: 26rpx;
  line-height: 1.8;
  color: var(--text-secondary);
}

.list-item {
  font-size: 26rpx;
  line-height: 1.8;
  color: var(--text-secondary);
  padding-left: 20rpx;
  position: relative;
}

.list-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 18rpx;
  width: 8rpx;
  height: 8rpx;
  background: var(--primary-color);
  border-radius: 50%;
}
</style>
