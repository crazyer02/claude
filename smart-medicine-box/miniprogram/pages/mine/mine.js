/**
 * 个人中心页
 */
const { userApi } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    userInfo: null,
    fontSizeMode: 'large',
    fontSizeLabels: {
      normal: '标准',
      large: '大号',
      xlarge: '特大',
    },
    appVersion: '1.0.0',
  },

  onShow() {
    const userInfo = app.globalData.userInfo || wx.getStorageSync('userInfo');
    this.setData({
      userInfo,
      fontSizeMode: app.globalData.fontSizeMode,
    });
  },

  /**
   * 微信登录
   */
  onLogin() {
    app.wxLogin((user) => {
      this.setData({ userInfo: user });
    });
  },

  /**
   * 设置字体大小
   */
  onSetFontSize(e) {
    const mode = e.currentTarget.dataset.mode;
    this.setData({ fontSizeMode: mode });
    app.setFontSizeMode(mode);
    wx.showToast({
      title: `已切换为${this.data.fontSizeLabels[mode]}字体`,
      icon: 'none',
      duration: 1500,
    });
  },

  /**
   * 编辑个人信息
   */
  onEditProfile() {
    wx.showActionSheet({
      itemList: ['修改昵称', '设置年龄', '设置紧急联系人', '修改备注/过敏信息'],
      success: (res) => {
        const fieldMap = ['nickname', 'age', 'emergency_contact', 'remark'];
        const field = fieldMap[res.tapIndex];
        const titles = ['输入新昵称', '输入年龄', '输入紧急联系人电话', '输入备注信息（过敏史等）'];

        wx.showModal({
          title: titles[res.tapIndex],
          editable: true,
          placeholderText: '请输入...',
          success: async (modalRes) => {
            if (modalRes.confirm && modalRes.content) {
              try {
                let value = modalRes.content;
                if (field === 'age') value = parseInt(value);
                const updateData = { [field]: value };
                await userApi.updateProfile(updateData);

                // 更新本地缓存
                const userInfo = { ...this.data.userInfo, ...updateData };
                app.globalData.userInfo = userInfo;
                wx.setStorageSync('userInfo', userInfo);
                this.setData({ userInfo });

                wx.showToast({ title: '✅ 已更新', icon: 'none' });
              } catch (err) {
                console.error('更新失败:', err);
              }
            }
          },
        });
      },
    });
  },

  /**
   * 订阅消息
   */
  onSubscribeMessage() {
    wx.requestSubscribeMessage({
      tmplIds: ['your-template-id-here'],
      success: () => {
        wx.showToast({ title: '订阅成功，将收到用药提醒', icon: 'success' });
      },
      fail: () => {
        wx.showToast({ title: '订阅失败，可在设置中开启', icon: 'none' });
      },
    });
  },

  /**
   * 页面跳转
   */
  goSchedule() {
    wx.navigateTo({ url: '/pages/schedule/schedule' });
  },
  goFamily() {
    wx.navigateTo({ url: '/pages/family/family' });
  },

  /**
   * 关于
   */
  onAbout() {
    wx.showModal({
      title: '关于智能药箱',
      content: '版本: 1.0.0\n\n智能药箱是一款专为老年人设计的用药提醒小程序。支持药品管理、定时提醒、家人远程查看等功能。',
      showCancel: false,
      confirmText: '知道了',
    });
  },
});
