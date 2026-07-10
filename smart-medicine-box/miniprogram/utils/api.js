/**
 * API 请求封装
 * 统一处理 token、错误提示、loading 状态
 */
const app = getApp();

/**
 * 通用请求方法
 * @param {string} url - API 路径 (不含 baseUrl)
 * @param {object} options - 请求选项
 * @returns {Promise}
 */
// 防止 showLoading/hideLoading 不配对
let loadingCount = 0;

function showLoad(title) {
  if (loadingCount === 0) {
    wx.showLoading({ title, mask: true });
  }
  loadingCount++;
}

function hideLoad() {
  if (loadingCount > 0) {
    loadingCount--;
    if (loadingCount === 0) {
      wx.hideLoading();
    }
  }
}

function request(url, options = {}) {
  const {
    method = 'GET',
    data = {},
    showLoading = false,
    loadingText = '加载中...',
    needAuth = true,
  } = options;

  if (showLoading) {
    showLoad(loadingText);
  }

  const header = {
    'Content-Type': 'application/json',
  };

  if (needAuth) {
    const token = wx.getStorageSync('token') || app.globalData.token;
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBaseUrl}${url}`,
      method,
      data,
      header,
      success: (res) => {
        if (showLoading) hideLoad();

        if (res.statusCode === 200) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          wx.removeStorageSync('token');
          wx.removeStorageSync('userInfo');
          app.globalData.token = null;
          app.globalData.userInfo = null;

          wx.showModal({
            title: '登录已过期',
            content: '请重新登录',
            showCancel: false,
            success: () => {
              app.wxLogin(() => {
                // 重试时不重复 showLoading
                request(url, { ...options, showLoading: false }).then(resolve).catch(reject);
              });
            },
          });
        } else {
          const msg = (res.data && res.data.detail) || '请求失败';
          wx.showToast({ title: msg, icon: 'none', duration: 2500 });
          reject(res);
        }
      },
      fail: (err) => {
        if (showLoading) hideLoad();
        wx.showToast({ title: '网络异常，请检查网络', icon: 'none', duration: 2500 });
        reject(err);
      },
    });
  });
}

/**
 * GET 请求
 */
function get(url, params = {}, options = {}) {
  const query = Object.keys(params)
    .filter((k) => params[k] !== undefined && params[k] !== null)
    .map((k) => `${k}=${encodeURIComponent(params[k])}`)
    .join('&');
  const fullUrl = query ? `${url}?${query}` : url;
  return request(fullUrl, { ...options, method: 'GET', data: {} });
}

/**
 * POST 请求
 */
function post(url, data = {}, options = {}) {
  return request(url, { ...options, method: 'POST', data });
}

/**
 * PUT 请求
 */
function put(url, data = {}, options = {}) {
  return request(url, { ...options, method: 'PUT', data });
}

/**
 * DELETE 请求
 */
function del(url, options = {}) {
  return request(url, { ...options, method: 'DELETE', data: {} });
}

// ==================== 用户 API ====================
const userApi = {
  login: (code) => post('/user/login', { code }, { needAuth: false }),
  getProfile: () => get('/user/profile'),
  updateProfile: (data) => put('/user/profile', data),
  bindFamily: (data) => post('/user/family/bind', data),
  getFamilyMembers: (elderlyUserId) => get('/user/family/members', { elderly_user_id: elderlyUserId }),
  getBindedElderly: () => get('/user/family/elderly'),
  getElderlyInfo: (elderlyId) => get(`/user/family/elderly/${elderlyId}`),
  getElderlyToday: (elderlyId) => get(`/user/family/elderly/${elderlyId}/today`),
};

// ==================== 药品 API ====================
const medicineApi = {
  getList: (isActive) => get('/medicines', { is_active: isActive }),
  getDetail: (id) => get(`/medicines/${id}`),
  create: (data) => post('/medicines', data, { showLoading: true, loadingText: '添加中...' }),
  update: (id, data) => put(`/medicines/${id}`, data, { showLoading: true, loadingText: '更新中...' }),
  delete: (id) => del(`/medicines/${id}`),
  getLowStock: () => get('/medicines/low-stock'),
};

// ==================== 用药计划 API ====================
const scheduleApi = {
  getList: (medicineId) => get('/schedules', { medicine_id: medicineId }),
  create: (data) => post('/schedules', data),
  update: (id, data) => put(`/schedules/${id}`, data),
  delete: (id) => del(`/schedules/${id}`),
};

// ==================== 用药记录 API ====================
const recordApi = {
  getList: (params) => get('/records', params),
  create: (data) => post('/records', data, { showLoading: true, loadingText: '记录中...' }),
  getToday: () => get('/today'),
};

module.exports = {
  userApi,
  medicineApi,
  scheduleApi,
  recordApi,
};
