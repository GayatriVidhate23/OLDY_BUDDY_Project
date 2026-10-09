import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { fetchApi } from '../../services/api';
import { useAuth } from '../../store/auth';

interface Elder {
  id: number;
  full_name: string;
}

interface ElderDashboardData {
  profile: any;
  status: any;
  reminders: any[];
}

export default function CaregiverHomeScreen() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  
  const [elders, setElders] = useState<Elder[]>([]);
  const [dashboardData, setDashboardData] = useState<Record<number, ElderDashboardData>>({});
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      // Get elders linked to this caregiver
      const eldersList = await fetchApi('/caregiver/elders');
      setElders(eldersList);

      const dataMap: Record<number, ElderDashboardData> = {};

      for (const elder of eldersList) {
        try {
          const [profile, status, reminders] = await Promise.all([
            fetchApi(`/v1/elders/${elder.id}`),
            fetchApi(`/v1/elders/${elder.id}/status`),
            fetchApi(`/v1/elders/${elder.id}/reminders`),
          ]);
          dataMap[elder.id] = { profile, status, reminders };
        } catch (e) {
          // Fallback if one elder fails
          dataMap[elder.id] = { profile: null, status: null, reminders: [] };
        }
      }

      setDashboardData(dataMap);
    } catch (e: any) {
      setErrorMsg(e.message || 'Could not load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const formatLastActive = (dateString: string) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours === 0) {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      return `${diffMins}m ago`;
    }
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Caregiver Dashboard</Text>
        <TouchableOpacity onPress={signOut} style={styles.signOutButton}>
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
      </View>

      {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}

      {loading ? (
        <ActivityIndicator size="large" color={theme.colors.primary} style={{ marginTop: 40 }} />
      ) : elders.length === 0 ? (
        <Text style={styles.emptyText}>You are not connected to any elders yet.</Text>
      ) : (
        elders.map((elder) => {
          const data = dashboardData[elder.id];
          const isSOS = data?.status?.status?.toLowerCase() === 'sos';
          
          return (
            <TouchableOpacity 
              key={elder.id} 
              style={styles.card}
              onPress={() => router.push(`/(caregiver)/elder-details?elderId=${elder.id}`)}
              activeOpacity={0.8}
            >
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>{elder.full_name}</Text>
                <TouchableOpacity 
                  style={styles.pairingButton}
                  onPress={() => router.push(`/(caregiver)/pairing?elderId=${elder.id}`)}
                >
                  <Text style={styles.pairingText}>Pairing Code</Text>
                </TouchableOpacity>
              </View>

              <View style={styles.statsRow}>
                <View style={[styles.statBox, isSOS ? styles.statBoxSOS : {}]}>
                  <Text style={styles.statLabel}>Status</Text>
                  <Text style={[styles.statValue, isSOS ? styles.textWhite : {}]}>
                    {data?.status?.status || 'Unknown'}
                  </Text>
                </View>
                <View style={styles.statBox}>
                  <Text style={styles.statLabel}>Last Active</Text>
                  <Text style={styles.statValue}>
                    {data?.profile?.last_interaction_at 
                      ? formatLastActive(data.profile.last_interaction_at)
                      : 'Never'}
                  </Text>
                </View>
              </View>

              <Text style={styles.sectionTitle}>Active Reminders</Text>
              {data?.reminders?.length === 0 ? (
                <Text style={styles.emptyReminders}>No active reminders.</Text>
              ) : (
                data?.reminders?.map((rem: any) => (
                  <View key={rem.id} style={styles.reminderItem}>
                    <Text style={styles.reminderTitle}>{rem.title}</Text>
                    <Text style={styles.reminderRecurrence}>{rem.recurrence}</Text>
                  </View>
                ))
              )}
            </TouchableOpacity>
          );
        })
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.lg,
    paddingTop: theme.spacing.xxl,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  signOutButton: {
    padding: theme.spacing.sm,
    backgroundColor: theme.colors.border,
    borderRadius: theme.roundness,
  },
  signOutText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  error: {
    color: theme.colors.error,
    marginBottom: theme.spacing.lg,
  },
  emptyText: {
    fontSize: 18,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginTop: 40,
  },
  card: {
    backgroundColor: theme.colors.background,
    borderRadius: theme.roundness,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.xl,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  pairingButton: {
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.roundness,
  },
  pairingText: {
    color: theme.colors.background,
    fontWeight: 'bold',
    fontSize: 14,
  },
  statsRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  statBox: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.roundness,
    alignItems: 'center',
  },
  statBoxSOS: {
    backgroundColor: theme.colors.error,
  },
  statLabel: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  textWhite: {
    color: theme.colors.background,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: theme.spacing.md,
    color: theme.colors.text,
  },
  emptyReminders: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    fontStyle: 'italic',
  },
  reminderItem: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.md,
    borderRadius: theme.roundness,
    marginBottom: theme.spacing.sm,
  },
  reminderTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 4,
  },
  reminderRecurrence: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  }
});
