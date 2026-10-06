import { authStore } from '../store/authStore';

const BASE_URL = 'http://localhost:8000/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = authStore.getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    authStore.logout();
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth APIs
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string, role = 'ELDER', fullName?: string) =>
    request<{ id: number; email: string; role: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, role, full_name: fullName }),
    }),

  getMe: () => request<{ id: number; email: string; role: string; full_name?: string }>('/users/me'),

  // Elder Profile APIs
  getElderProfile: (elderId: number) =>
    request<{ id: number; user_id: number; preferences: any; medical_info: any; emergency_contact?: string }>(`/elders/${elderId}`),

  updateElderProfile: (elderId: number, data: { preferences?: any; medical_info?: any; emergency_contact?: string }) =>
    request<any>(`/elders/${elderId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // Activities & Reminders APIs
  getActivities: (elderId: number, type?: string) =>
    request<Array<{ id: number; elder_id: number; activity_type: string; description: string; status: string; timestamp: string }>>(
      `/elders/${elderId}/activities${type ? `?activity_type=${type}` : ''}`
    ),

  createActivity: (elderId: number, activity: { activity_type: string; description?: string; status?: string }) =>
    request<any>(`/elders/${elderId}/activities`, {
      method: 'POST',
      body: JSON.stringify(activity),
    }),

  updateActivityStatus: (activityId: number, status: string) =>
    request<any>(`/activities/${activityId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    }),

  triggerSOS: (elderId: number) =>
    request<any>(`/elders/${elderId}/sos`, { method: 'POST' }),

  // AI Conversation API
  sendChatMessage: (prompt: string, elderId?: number) =>
    request<{ reply: string; timestamp: string }>('/conversation', {
      method: 'POST',
      body: JSON.stringify({ prompt, elder_id: elderId }),
    }),
};
