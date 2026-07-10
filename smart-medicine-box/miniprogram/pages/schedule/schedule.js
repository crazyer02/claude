/**
 * 用药计划页面
 */
const { scheduleApi } = require('../../utils/api');
const { getPeriodLabel, getPeriodIcon, showConfirm } = require('../../utils/util');

Page({
  data: {
    medicineId: null,
    schedules: [],
    loading: false,
  },

  onLoad(options) {
    if (options.medicine_id) {
      this.setData({ medicineId: parseInt(options.medicine_id) });
    }
  },

  onShow() {
    this.loadSchedules();
  },

  async loadSchedules() {
    this.setData({ loading: true });
    try {
      const schedules = await scheduleApi.getList(this.data.medicineId);
      this.setData({ schedules });
    } catch (err) {
      console.error('加载用药计划失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  goAddSchedule() {
    const mid = this.data.medicineId;
    const url = mid ? `/pages/schedule/add/add?medicine_id=${mid}` : '/pages/schedule/add/add';
    wx.navigateTo({ url });
  },

  async onDeleteSchedule(e) {
    const id = e.currentTarget.dataset.id;
    const confirmed = await showConfirm({ title: '确认删除', content: '确定要删除这条用药计划吗？' });
    if (confirmed) {
      try {
        await scheduleApi.delete(id);
        wx.showToast({ title: '已删除', icon: 'success' });
        this.loadSchedules();
      } catch (err) {
        console.error('删除失败:', err);
      }
    }
  },

  onEditSchedule(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/schedule/add/add?id=${id}` });
  },
});
