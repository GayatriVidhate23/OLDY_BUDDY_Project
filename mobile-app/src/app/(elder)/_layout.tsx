import { useEffect, useState } from 'react';
import { Stack, useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';

export default function ElderLayout() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const checkConsent = async () => {
      const hasConsented = await SecureStore.getItemAsync('has_consented');
      if (!hasConsented) {
        router.replace('/(elder)/consent');
      }
      setChecked(true);
    };
    checkConsent();
  }, []);

  if (!checked) return null;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="home" />
      <Stack.Screen name="consent" />
    </Stack>
  );
}
