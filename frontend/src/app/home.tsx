
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { useStore } from '../store/store';
import { apiClient } from '../services/api';
import { LargeButton } from '../components/LargeButton';
import { useQuery, useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';

export default function Home() {
  const userId = useStore((state: any) => state.userId);
  const logout = useStore((state: any) => state.logout);

  const { data: profile } = useQuery({
    queryKey: ['profile', userId],
    queryFn: async () => (await apiClient.get(`/elders/${userId}/profile`)).data,
    enabled: !!userId
  });

  const sosMutation = useMutation({
    mutationFn: async () => (await apiClient.post(`/elders/${userId}/activities`, { activity_type: 'SOS', description: 'Help requested' })).data,
    onSuccess: () => Alert.alert("Help is on the way!", "Caregivers notified."),
    onError: () => Alert.alert("Error", "Could not send SOS!")
  });

  const handleLogout = () => { logout(); router.replace('/login'); };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.greeting}>Good Morning, Sunita</Text>
      
      <View style={styles.cardLime}>
        <Text style={styles.sectionTitleDark}>Today's Reminders</Text>
        <Text style={styles.infoDark}>• Medicine</Text>
        <Text style={styles.infoDark}>• Lunch</Text>
        <Text style={styles.infoDark}>• Doctor appointment</Text>
      </View>
      
      <LargeButton title="🎤 Talk to Oldy Buddy" variant="primary" onPress={() => router.push('/chat')} />
      <LargeButton title="🆘 I Need Help" variant="red" onPress={() => sosMutation.mutate()} />
      <LargeButton title="👤 Profile" variant="dark" onPress={() => router.push('/profile')} />
      <LargeButton title="🚪 Logout" variant="dark" onPress={handleLogout} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  content: { padding: 24, paddingTop: 60 },
  greeting: { fontSize: 40, fontWeight: '800', marginBottom: 40, color: '#111827' },
  cardLime: { 
    backgroundColor: '#ccff00', 
    padding: 32, 
    borderRadius: 32, 
    marginBottom: 40,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 12
  },
  sectionTitleDark: { fontSize: 28, fontWeight: '700', marginBottom: 16, color: '#111827' },
  infoDark: { fontSize: 22, marginBottom: 12, color: '#111827', fontWeight: '500' }
});
