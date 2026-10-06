import React, { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { authStore } from '../store/authStore';

export default function IndexScreen() {
  const router = useRouter();

  useEffect(() => {
    if (authStore.isAuthenticated()) {
      router.replace('/home');
    } else {
      router.replace('/login');
    }
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#4f46e5" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },
});
