import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useStore } from '../store/store';

const queryClient = new QueryClient();

export default function RootLayout() {
  const hydrate = useStore((state: any) => state.hydrate);

  useEffect(() => { hydrate(); }, [hydrate]);

  return (
    <QueryClientProvider client={queryClient}>
      <Stack screenOptions={{ headerStyle: { backgroundColor: '#FFF' }, headerTintColor: '#000' }}>
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="login" options={{ title: 'Login' }} />
        <Stack.Screen name="home" options={{ headerShown: false }} />
      </Stack>
    </QueryClientProvider>
  );
}
