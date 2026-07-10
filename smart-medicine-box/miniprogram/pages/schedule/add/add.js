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
    weekActive: { '1': false, '2': false, '3': false, '4': false, '5': false, '6': false, '7': false },
    submitting: false,
  },

  // 同步 selectedWeeks 数组 ↔ weekActive 对象
  syncWeekActive(arr) {
    const weekActive = { '1': false, '2': false, '3': false, '4': false, '5': false, '6': false, '7': false };
    (arr || []).forEach(v => { weekActive[v] = true; });
    return weekActive;
  },

  onLoad(options) {
    if (options.id) {
      const sid = parseInt(options.id);
      this.setData({ isEdit: true, scheduleId: sid });
      wx.setNavigationBarTitle({ title: '编辑用药计划' });
      this.loadSchedule(sid);
    }
    if (options.medicine_id) {
      this.setData({ 'form.medicine_id': parseInt(options.medicine_id) });
    }
  },

  onShow() {
    this.setData({ fontSizeMode: app.globalData.fontSizeMode || 'large' });
    this.loadMedicines();
  },

  async loadSchedule(sid) {
    try {
      const schedules = await scheduleApi.getList();
      const s = schedules.find(item => item.id === sid);
      console.log('loadSchedule found:', s);
      if (s) {
        const dows = s.days_of_week || '';
        const arr = dows ? dows.split(',').map(v => v.trim()).filter(Boolean) : [];
        console.log('days_of_week raw:', JSON.stringify(s.days_of_week), 'arr:', arr);
        this.setData({
          'form.medicine_id': s.medicine_id,
          'form.medicine_name': s.medicine_name || '',
          'form.period': s.period || 'morning',
          'form.time_label': s.time_label || '',
          'form.reminder_time': s.reminder_time || '08:00',
          'form.dosage_at_time': s.dosage_at_time || '',
          'form.days_of_week': dows,
          weekActive: this.syncWeekActive(arr),
        });
      } else {
        console.error('schedule not found, sid:', sid, 'list:', schedules.map(x => x.id));
      }
    } catch (err) {
      console.error('loadSchedule error:', err);
    }
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
    const val = String(e.currentTarget.dataset.val);
    const weekActive = { ...this.data.weekActive };
    weekActive[val] = !weekActive[val];
    const selected = Object.keys(weekActive).filter(k => weekActive[k]);
    this.setData({
      weekActive,
      'form.days_of_week': selected.sort().join(','),
    });
  },

  async onSubmit() {
    // 防止重复提交
    if (this.data.submitting) return;
    this.data.submitting = true;

    const form = this.data.form;
    if (!form.medicine_id) {
      wx.showToast({ title: '请选择药品', icon: 'none' });
      this.data.submitting = false;
      return;
    }
    if (!form.reminder_time) {
      wx.showToast({ title: '请选择提醒时间', icon: 'none' });
      this.data.submitting = false;
      return;
    }
    if (!form.dosage_at_time) {
      wx.showToast({ title: '请输入该时段用量', icon: 'none' });
      this.data.submitting = false;
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
