import { View, Text, StyleSheet } from 'react-native';
import { useStore } from '../store/store';
import { apiClient } from '../services/api';
import { LargeButton } from '../components/LargeButton';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';

export default function Profile() {
  const userId = useStore((state: any) => state.userId);

  const { data: profile } = useQuery({
    queryKey: ['profile', userId],
    queryFn: async () => (await apiClient.get(`/elders/${userId}/profile`)).data,
    enabled: !!userId
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>My Profile</Text>
      </View>
      
      <View style={styles.content}>
        <View style={styles.card}>
          <Text style={styles.label}>Emergency Contact</Text>
          <Text style={styles.value}>{profile?.emergency_contact || 'Not set'}</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Preferences</Text>
          <Text style={styles.value}>
            {profile?.preferences ? JSON.stringify(profile.preferences, null, 2) : 'No specific preferences'}
          </Text>
        </View>

        <LargeButton title="Go Back" variant="primary" onPress={() => router.replace('/home')} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  header: { padding: 24, paddingTop: 60, backgroundColor: '#0ea5e9' },
  headerText: { fontSize: 32, fontWeight: '800', color: '#ffffff' },
  content: { padding: 24 },
  card: { backgroundColor: '#ffffff', padding: 24, borderRadius: 24, marginBottom: 24, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 8 },
  label: { fontSize: 20, color: '#6b7280', marginBottom: 8, fontWeight: '600' },
  value: { fontSize: 24, color: '#111827', fontWeight: '500' }
});
