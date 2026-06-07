const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const REQUEST_TIMEOUT_MS = 15000;

async function request(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const { headers: extraHeaders, body, ...restOptions } = options;

  try {
    const response = await fetch(`${API_URL}${path}`, {
      credentials: 'include',
      signal: controller.signal,
      body,
      headers: {
        ...(body && !(body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
        ...extraHeaders,
      },
      ...restOptions,
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const errBody = await response.json();
        detail = typeof errBody.detail === 'string' ? errBody.detail : detail;
      } catch {
        /* if response body is not JSON */
      }
      const err = new Error(detail);
      err.status = response.status;
      throw err;
    }

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      const err = new Error(`Unexpected non-JSON response from ${path}`);
      err.status = response.status;
      throw err;
    }
    return response.json();
  } catch (err) {
    if (err.name === 'AbortError') throw new Error('İstek zaman aşımına uğradı');
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export const auth = {
  register: (data) => request('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  login: (data) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  logout: () => request('/auth/logout', { method: 'POST' }),

  me: () => request('/auth/me'),

  deleteAccount: () => request('/auth/me', { method: 'DELETE' }),

  updateUsername: (data) => request('/auth/me', { method: 'PATCH', body: JSON.stringify(data) }),

  verifyEmail: (data) => request('/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  resendVerification: (data) => request('/auth/resend-verification', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

export const scans = {
  predict: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/scans/predict', {
      method: 'POST',
      body: formData,
    });
  },

  list: () => request('/scans/'),

  get: (scanId) => request(`/scans/${scanId}`),

  delete: (scanId) => request(`/scans/${scanId}`, { method: 'DELETE' }),

  reportUrl: (scanId) => `${API_URL}/scans/${scanId}/report`,
};
