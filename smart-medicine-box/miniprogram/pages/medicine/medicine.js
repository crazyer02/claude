/**
 * 我的药品页面
 */
const { medicineApi } = require('../../utils/api');
const { showConfirm } = require('../../utils/util');

Page({
  data: {
    medicines: [],
    lowStockMedicines: [],
    loading: false,
    showLowStockAlert: false,
  },

  onShow() {
    this.loadMedicines();
  },

  onPullDownRefresh() {
    this.loadMedicines().then(() => wx.stopPullDownRefresh());
  },

  async loadMedicines() {
    this.setData({ loading: true });
    try {
      const [medRes, lowRes] = await Promise.all([
        medicineApi.getList(true),
        medicineApi.getLowStock(),
      ]);
      this.setData({
        medicines: medRes.items || [],
        lowStockMedicines: lowRes.items || [],
        showLowStockAlert: (lowRes.items || []).length > 0,
      });
    } catch (err) {
      console.error('加载药品失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 跳转添加药品
   */
  goAddMedicine() {
    wx.navigateTo({ url: '/pages/medicine/add/add' });
  },

  /**
   * 查看药品详情/编辑
   */
  goEditMedicine(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/medicine/add/add?id=${id}` });
  },

  /**
   * 删除药品
   */
  async onDeleteMedicine(e) {
    const id = e.currentTarget.dataset.id;
    const confirmed = await showConfirm({
      title: '确认删除',
      content: '确定要删除这个药品吗？',
    });
    if (confirmed) {
      try {
        await medicineApi.delete(id);
        wx.showToast({ title: '已删除', icon: 'success' });
        this.loadMedicines();
      } catch (err) {
        console.error('删除失败:', err);
      }
    }
  },

  /**
   * 跳转用药计划
   */
  goSchedule(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/schedule/schedule?medicine_id=${id}` });
  },

  /**
   * 库存 +1
   */
  async onStockAdd(e) {
    const medicine = e.currentTarget.dataset.medicine;
    try {
      await medicineApi.update(medicine.id, {
        total_stock: medicine.total_stock + 1,
      });
      this.loadMedicines();
    } catch (err) {
      console.error('更新库存失败:', err);
    }
  },
});
