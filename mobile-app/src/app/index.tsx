import { useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { theme } from '../theme';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';
import { useAuth } from '../store/auth';

export default function Index() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [langChecked, setLangChecked] = useState(false);

  useEffect(() => {
    if (isLoading) return;

    const checkLang = async () => {
      const pref = await SecureStore.getItemAsync('language_pref');
      if (!pref) {
        router.replace('/(auth)/language');
      } else {
        // If language is set, rely on AuthProvider to redirect
        // AuthProvider automatically redirects to login if user is null
        // However, if we're at index and user is null, AuthProvider might have already triggered.
        // To be safe, we explicitly go to login if user is null
        if (!user) {
           router.replace('/(auth)/login');
        }
      }
      setLangChecked(true);
    };

    checkLang();
  }, [isLoading, user]);

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.background }}>
      <ActivityIndicator size="large" color={theme.colors.primary} />
    </View>
  );
}
