import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { theme } from '../../theme';
import { fetchApi } from '../../services/api';
import { BigButton } from '../../components/BigButton';

export default function CaregiverAlertsScreen() {
  const { elderId } = useLocalSearchParams<{ elderId: string }>();
  const router = useRouter();

  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    loadAlerts();
  }, [elderId]);

  const loadAlerts = async () => {
    if (!elderId) return;
    setLoading(true);
    try {
      const data = await fetchApi(`/v1/elders/${elderId}/alerts?status=open`);
      setAlerts(data);
    } catch (e: any) {
      setErrorMsg(e.message || 'Could not load alerts.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (alertId: number) => {
    setActionLoading(alertId);
    try {
      await fetchApi(`/v1/alerts/${alertId}/verify`, { method: 'POST', body: JSON.stringify({}) });
      await loadAlerts();
    } catch (e: any) {
      setErrorMsg(e.message || 'Verification failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolve = async (alertId: number) => {
    setActionLoading(alertId);
    try {
      await fetchApi(`/v1/alerts/${alertId}/resolve`, { method: 'POST' });
      await loadAlerts();
    } catch (e: any) {
      setErrorMsg(e.message || 'Resolution failed.');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Active Alerts</Text>

      {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}

      {loading ? (
        <ActivityIndicator size="large" color={theme.colors.error} style={{ marginTop: 40 }} />
      ) : alerts.length === 0 ? (
        <Text style={styles.emptyText}>No active alerts. Everything is fine.</Text>
      ) : (
        alerts.map((alert) => (
          <View key={alert.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>{alert.title || 'Unknown Alert'}</Text>
              <Text style={styles.severity}>{alert.severity}</Text>
            </View>
            <Text style={styles.details}>{alert.details}</Text>
            
            <View style={styles.buttonContainer}>
              {actionLoading === alert.id ? (
                <ActivityIndicator size="small" color={theme.colors.primary} />
              ) : (
                <>
                  <BigButton 
                    title="Verify (SOS)" 
                    onPress={() => handleVerify(alert.id)}
                    style={{ flex: 1, minHeight: 60 }}
                    textStyle={{ fontSize: 16 }}
                  />
                  <BigButton 
                    title="Resolve" 
                    onPress={() => handleResolve(alert.id)}
                    variant="secondary"
                    style={{ flex: 1, minHeight: 60 }}
                    textStyle={{ fontSize: 16 }}
                  />
                </>
              )}
            </View>
          </View>
        ))
      )}

      <BigButton 
        title="Back" 
        onPress={() => router.back()} 
        variant="secondary"
        style={{ marginTop: theme.spacing.xxl }}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.xl,
    paddingTop: theme.spacing.xxl * 2,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  error: {
    color: theme.colors.error,
    textAlign: 'center',
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
    padding: theme.spacing.lg,
    borderRadius: theme.roundness,
    marginBottom: theme.spacing.lg,
    borderLeftWidth: 6,
    borderLeftColor: theme.colors.error,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
    flex: 1,
  },
  severity: {
    fontSize: 14,
    fontWeight: 'bold',
    color: theme.colors.error,
    textTransform: 'uppercase',
  },
  details: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.lg,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  }
});
