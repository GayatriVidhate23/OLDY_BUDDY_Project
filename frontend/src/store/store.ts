import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const setItem = async (key: string, value: string) => Platform.OS === 'web' ? localStorage.setItem(key, value) : await SecureStore.setItemAsync(key, value);
const getItem = async (key: string) => Platform.OS === 'web' ? localStorage.getItem(key) : await SecureStore.getItemAsync(key);
const removeItem = async (key: string) => Platform.OS === 'web' ? localStorage.removeItem(key) : await SecureStore.deleteItemAsync(key);

export const useStore = create<any>((set) => ({
  token: null,
  userId: null,
  setAuth: async (token: string, userId: number) => {
    await setItem('token', token);
    await setItem('userId', userId.toString());
    set({ token, userId });
  },
  logout: async () => {
    await removeItem('token');
    await removeItem('userId');
    set({ token: null, userId: null });
  },
  hydrate: async () => {
    const token = await getItem('token');
    const userId = await getItem('userId');
    if (token && userId) set({ token, userId: parseInt(userId) });
  }
}));
