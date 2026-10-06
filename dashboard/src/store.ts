import { create } from 'zustand';
import { apiClient } from './api';

export const useStore = create<any>((set) => ({
  token: localStorage.getItem('token'),
  role: localStorage.getItem('role'),
  userId: localStorage.getItem('userId'),
  
  setAuth: async (token: string) => {
    localStorage.setItem('token', token);
    
    // Fetch user details to get role
    try {
      const res = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const user = res.data;
      localStorage.setItem('role', user.role);
      localStorage.setItem('userId', user.id);
      set({ token, role: user.role, userId: user.id });
    } catch (err) {
      console.error(err);
    }
  },
  
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('userId');
    set({ token: null, role: null, userId: null });
  }
}));
