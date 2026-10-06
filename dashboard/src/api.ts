const BASE_URL = 'http://localhost:8000/api/v1';

let authToken: string | null = localStorage.getItem('caregiver_token');

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('caregiver_token', token);
  } else {
    localStorage.removeItem('caregiver_token');
  }
};

export const getAuthToken = () => authToken;

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}

export const dashboardApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request<{ id: number; email: string; role: string; full_name?: string }>('/users/me'),

  getDashboardOverview: (elderId: number) =>
    request<{
      elder_id: number;
      elder_name: string;
      elder_email: string;
      emergency_contact?: string;
      last_check_in?: string;
      last_interaction?: string;
      status_badge: string;
      active_alerts_count: number;
      today_reminders_count: number;
      completed_reminders_count: number;
      missed_reminders_count: number;
    }>(`/dashboard/overview/${elderId}`),

  getActivities: (elderId: number) =>
    request<Array<{ id: number; elder_id: number; activity_type: string; description: string; status: string; timestamp: string }>>(
      `/elders/${elderId}/activities`
    ),

  createActivity: (elderId: number, activity: { activity_type: string; description: string }) =>
    request<any>(`/elders/${elderId}/activities`, {
      method: 'POST',
      body: JSON.stringify(activity),
    }),

  updateActivityStatus: (activityId: number, status: string) =>
    request<any>(`/activities/${activityId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    }),

  triggerOutboundCall: (elderId: number) =>
    request<any>('/voice/outbound-call', {
      method: 'POST',
      body: JSON.stringify({ elder_id: elderId, call_type: 'OUTBOUND_CHECKIN' }),
    }),

  getVoiceHistory: (elderId: number) =>
    request<Array<{ id: number; elder_id: number; phone_number: string; call_type: string; status: string; duration_seconds: number; transcript: string; ai_summary: string; timestamp: string }>>(
      `/voice/history/${elderId}`
    ),

  getAlerts: (elderId: number) =>
    request<Array<{ id: number; elder_id: number; severity: string; message: string; is_resolved: boolean; timestamp: string }>>(
      `/alerts/${elderId}`
    ),

  resolveAlert: (alertId: number) =>
    request<any>(`/alerts/${alertId}/resolve`, {
      method: 'PUT',
    }),

  getElderProfile: (elderId: number) => request<any>(`/elders/${elderId}`),

  updateElderProfile: (elderId: number, data: any) =>
    request<any>(`/elders/${elderId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};
