/**
 * 字体大小 Behavior - 所有页面混入即可响应字体切换
 */
const app = getApp();

module.exports = Behavior({
  data: {
    fontSizeMode: 'large',
  },

  lifetimes: {
    attached() {
      this.setData({ fontSizeMode: app.globalData.fontSizeMode || 'large' });
    },
  },

  pageLifetimes: {
    show() {
      this.setData({ fontSizeMode: app.globalData.fontSizeMode || 'large' });
    },
  },
});
