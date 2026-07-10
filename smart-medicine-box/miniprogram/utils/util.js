/**
 * 通用工具函数
 */

/**
 * 格式化时间
 * @param {Date|string} date
 * @param {string} format - 'HH:MM' | 'YYYY-MM-DD' | 'MM-DD HH:MM'
 */
function formatTime(date, format = 'HH:MM') {
  if (typeof date === 'string') {
    date = new Date(date.replace(/-/g, '/'));
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');

  switch (format) {
    case 'HH:MM':
      return `${hour}:${minute}`;
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`;
    case 'MM-DD HH:MM':
      return `${month}-${day} ${hour}:${minute}`;
    default:
      return `${year}-${month}-${day} ${hour}:${minute}`;
  }
}

/**
 * 获取今天的日期字符串
 */
function getTodayStr() {
  return formatDateStr(new Date());
}

/**
 * 格式化日期为 YYYY-MM-DD
 */
function formatDateStr(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/**
 * 获取时间段的中文名称
 */
function getPeriodLabel(period) {
  const map = {
    morning: '早上',
    noon: '中午',
    evening: '晚上',
    night: '睡前',
  };
  return map[period] || period;
}

/**
 * 获取时间段图标
 */
function getPeriodIcon(period) {
  const map = {
    morning: '🌅',
    noon: '☀️',
    evening: '🌇',
    night: '🌙',
  };
  return map[period] || '💊';
}

/**
 * 获取状态配置（颜色、文字）
 */
function getStatusConfig(status) {
  const configs = {
    taken: { text: '已服用', color: '#52C41A', bg: '#F6FFED', icon: '✓' },
    missed: { text: '未服用', color: '#FF4D4F', bg: '#FFF2F0', icon: '✗' },
    skipped: { text: '已跳过', color: '#FAAD14', bg: '#FFFBE6', icon: '—' },
    pending: { text: '待服用', color: '#4A90D9', bg: '#E6F4FF', icon: '○' },
  };
  return configs[status] || configs.pending;
}

/**
 * 显示确认对话框（大字体，适合老年人）
 */
function showConfirm(options) {
  return new Promise((resolve) => {
    wx.showModal({
      title: options.title || '提示',
      content: options.content || '',
      confirmText: options.confirmText || '确定',
      cancelText: options.cancelText || '取消',
      confirmColor: '#4A90D9',
      success: (res) => {
        resolve(res.confirm);
      },
    });
  });
}

/**
 * 防抖
 */
function debounce(fn, delay = 300) {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * 简单的语音播报（使用 wx.createInnerAudioContext 或 TTS）
 * 实际项目中可接入微信同声传译插件
 */
function speakText(text) {
  // 微信小程序可通过插件实现 TTS
  // plugin://wx069ba97219f66d99/speak
  console.log('[语音播报]', text);
}

module.exports = {
  formatTime,
  getTodayStr,
  formatDateStr,
  getPeriodLabel,
  getPeriodIcon,
  getStatusConfig,
  showConfirm,
  debounce,
  speakText,
};
