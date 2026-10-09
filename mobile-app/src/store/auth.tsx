import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { useRouter, useSegments } from 'expo-router';
import { fetchApi } from '../services/api';

type Role = 'ELDER' | 'CAREGIVER' | 'ADMIN' | 'FAMILY';

interface User {
  id: number;
  email: string;
  role: Role;
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  signIn: (token: string, refreshToken: string) => Promise<void>;
  signOut: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const segments = useSegments();

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        const userData = await fetchApi('/auth/me');
        setUser(userData);
      }
    } catch (e) {
      console.log('Failed to load user', e);
      await SecureStore.deleteItemAsync('access_token');
      await SecureStore.deleteItemAsync('refresh_token');
    } finally {
      setIsLoading(false);
    }
  };

  const signIn = async (token: string, refreshToken: string) => {
    await SecureStore.setItemAsync('access_token', token);
    await SecureStore.setItemAsync('refresh_token', refreshToken);
    await loadUser();
  };

  const signOut = async () => {
    try {
      await fetchApi('/auth/logout', { method: 'POST' });
    } catch (e) {
      // Ignore errors on logout
    }
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    setUser(null);
  };

  // Route guarding
  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === '(auth)';
    const inElderGroup = segments[0] === '(elder)';
    const inCaregiverGroup = segments[0] === '(caregiver)';

    if (!user && !inAuthGroup) {
      // Redirect to login if not authenticated
      router.replace('/(auth)/login');
    } else if (user) {
      // Role-based routing guard
      if (user.role === 'ELDER' && !inElderGroup) {
        router.replace('/(elder)/home');
      } else if (user.role === 'CAREGIVER' && !inCaregiverGroup) {
        router.replace('/(caregiver)/home');
      } else if (user.role !== 'ELDER' && user.role !== 'CAREGIVER') {
        // ADMIN / FAMILY not supported yet
        if (!inAuthGroup) router.replace('/(auth)/login');
      }
    }
  }, [user, isLoading, segments]);

  return (
    <AuthContext.Provider value={{ user, isLoading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
