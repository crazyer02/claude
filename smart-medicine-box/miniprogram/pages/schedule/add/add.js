/**
 * 添加/编辑用药计划
 */
const app = getApp();
const { scheduleApi, medicineApi } = require('../../../utils/api');

Page({
  data: {
    fontSizeMode: 'large',
    isEdit: false,
    scheduleId: null,
    medicines: [],
    form: {
      medicine_id: null,
      medicine_name: '',
      period: 'morning',
      time_label: '',
      reminder_time: '08:00',
      dosage_at_time: '',
      days_of_week: '',
    },
    periodOptions: [
      { value: 'morning', label: '早上', icon: '🌅' },
      { value: 'noon', label: '中午', icon: '☀️' },
      { value: 'evening', label: '晚上', icon: '🌇' },
      { value: 'night', label: '睡前', icon: '🌙' },
    ],
    timeLabels: {
      morning: ['早饭前', '早饭后'],
      noon: ['午饭前', '午饭后'],
      evening: ['晚饭前', '晚饭后'],
      night: ['睡前半小时', '睡前'],
    },
    weekOptions: [
      { value: '1', label: '周一' }, { value: '2', label: '周二' },
      { value: '3', label: '周三' }, { value: '4', label: '周四' },
      { value: '5', label: '周五' }, { value: '6', label: '周六' },
      { value: '7', label: '周日' },
    ],
    selectedWeeks: [],
    submitting: false,
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ isEdit: true, scheduleId: parseInt(options.id) });
      wx.setNavigationBarTitle({ title: '编辑用药计划' });
    }
    if (options.medicine_id) {
      this.setData({ 'form.medicine_id': parseInt(options.medicine_id) });
    }
  },

  onShow() {
    this.setData({ fontSizeMode: app.globalData.fontSizeMode || 'large' });
    this.loadMedicines();
  },

  goAddMedicine() {
    wx.navigateTo({ url: '/pages/medicine/add/add' });
  },

  async loadMedicines() {
    try {
      const res = await medicineApi.getList(true);
      const medicines = res.items || [];
      console.log('加载药品列表:', medicines.length, '个');
      this.setData({ medicines });
    } catch (err) {
      console.error('加载药品列表失败:', err);
      wx.showToast({ title: '加载药品失败，请返回重试', icon: 'none' });
    }
  },

  onSelectMedicine(e) {
    const id = parseInt(e.currentTarget.dataset.id);
    const name = e.currentTarget.dataset.name;
    console.log('选择药品:', id, name);
    this.setData({
      'form.medicine_id': id,
      'form.medicine_name': name,
    });
  },

  onSelectPeriod(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ 'form.period': value });
  },

  onSelectTimeLabel(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ 'form.time_label': value });
  },

  onTimeChange(e) {
    this.setData({ 'form.reminder_time': e.detail.value });
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onToggleWeek(e) {
    const value = e.currentTarget.dataset.value;
    let selected = [...this.data.selectedWeeks];
    const idx = selected.indexOf(value);
    if (idx >= 0) {
      selected.splice(idx, 1);
    } else {
      selected.push(value);
    }
    this.setData({
      selectedWeeks: selected,
      'form.days_of_week': selected.sort().join(','),
    });
  },

  async onSubmit() {
    const form = this.data.form;
    if (!form.medicine_id) {
      wx.showToast({ title: '请选择药品', icon: 'none' });
      return;
    }
    if (!form.reminder_time) {
      wx.showToast({ title: '请选择提醒时间', icon: 'none' });
      return;
    }
    if (!form.dosage_at_time) {
      wx.showToast({ title: '请输入该时段用量', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });
    try {
      if (this.data.isEdit) {
        await scheduleApi.update(this.data.scheduleId, form);
        wx.showToast({ title: '✅ 更新成功', icon: 'none' });
      } else {
        await scheduleApi.create(form);
        wx.showToast({ title: '✅ 创建成功', icon: 'none' });
      }
      setTimeout(() => wx.navigateBack(), 1500);
    } catch (err) {
      console.error('提交失败:', err);
    } finally {
      this.setData({ submitting: false });
    }
  },
});
