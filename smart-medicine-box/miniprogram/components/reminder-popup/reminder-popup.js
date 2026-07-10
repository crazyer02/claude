/**
 * 服药确认弹窗组件
 * 大字体、大按钮，方便老年人操作
 *
 * 属性:
 *   show     - 是否显示
 *   medicine - 药品信息对象
 *
 * 事件:
 *   confirm  - 确认服药
 *   skip     - 跳过
 *   close    - 关闭弹窗
 */
Component({
  properties: {
    show: {
      type: Boolean,
      value: false,
    },
    medicine: {
      type: Object,
      value: null,
    },
  },

  methods: {
    onConfirm() {
      this.triggerEvent('confirm');
    },

    onSkip() {
      this.triggerEvent('skip');
    },

    onClose() {
      this.triggerEvent('close');
    },

    // 阻止冒泡
    preventBubble() {},
  },
});
