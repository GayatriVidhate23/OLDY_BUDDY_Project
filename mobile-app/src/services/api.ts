import * as SecureStore from 'expo-secure-store';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = await SecureStore.getItemAsync('access_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // We will handle 401 via a global event or callback in the auth store
    // For now, throw an error to signal auth failure
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'API request failed');
  }

  return response.json();
}
