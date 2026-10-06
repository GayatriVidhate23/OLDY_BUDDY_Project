import { Redirect } from 'expo-router';
import { useStore } from '../store/store';
import { View, ActivityIndicator } from 'react-native';
import { useEffect, useState } from 'react';

export default function Index() {
  const token = useStore((state: any) => state.token);
  const [loading, setLoading] = useState(true);

  useEffect(() => { setTimeout(() => setLoading(false), 500); }, []);

  if (loading) return <View style={{flex: 1, justifyContent: 'center'}}><ActivityIndicator size="large" /></View>;
  return token ? <Redirect href="/home" /> : <Redirect href="/login" />;
}
