/**
 * 家人绑定页 - 子女绑定老人，远程查看用药情况
 */
const { userApi } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    fontSizeMode: 'large',
    userType: 'elderly', // 'elderly' | 'family'
    bindedElderly: [],
    familyMembers: [],
    loading: false,
    // 绑定表单
    showBindForm: false,
    elderlyUserId: '',
    relationship: 'son',
    relationOptions: [
      { value: 'son', label: '儿子' },
      { value: 'daughter', label: '女儿' },
      { value: 'spouse', label: '配偶' },
      { value: 'grandson', label: '孙子' },
      { value: 'granddaughter', label: '孙女' },
      { value: 'other', label: '其他' },
    ],
  },

  onShow() {
    this.setData({ fontSizeMode: app.globalData.fontSizeMode || 'large' });
    this.loadData();
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      const userInfo = app.globalData.userInfo;
      if (userInfo && userInfo.is_elderly) {
        // 老年用户：查看自己的绑定家人
        this.setData({ userType: 'elderly' });
        const members = await userApi.getFamilyMembers(userInfo.id);
        this.setData({ familyMembers: members || [] });
      } else {
        // 子女用户：查看绑定的老人
        this.setData({ userType: 'family' });
        const elderly = await userApi.getBindedElderly();
        this.setData({ bindedElderly: elderly || [] });
      }
    } catch (err) {
      console.error('加载家人信息失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  showBind() {
    this.setData({ showBindForm: true });
  },

  hideBind() {
    this.setData({ showBindForm: false });
  },

  onElderlyIdInput(e) {
    this.setData({ elderlyUserId: e.detail.value });
  },

  onSelectRelation(e) {
    this.setData({ relationship: e.currentTarget.dataset.value });
  },

  async onSubmitBind() {
    const { elderlyUserId, relationship } = this.data;
    if (!elderlyUserId) {
      wx.showToast({ title: '请输入老人用户ID', icon: 'none' });
      return;
    }
    try {
      await userApi.bindFamily({
        elderly_user_id: parseInt(elderlyUserId),
        relationship,
      });
      wx.showToast({ title: '✅ 绑定成功', icon: 'none', duration: 2000 });
      this.setData({ showBindForm: false, elderlyUserId: '' });
      this.loadData();
    } catch (err) {
      console.error('绑定失败:', err);
    }
  },

  /**
   * 查看老人用药详情
   */
  goElderlyDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/index/index?elderly_id=${id}` });
  },
});
