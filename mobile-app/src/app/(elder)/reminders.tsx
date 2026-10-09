import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { useTranslation } from '../../i18n';
import { BigButton } from '../../components/BigButton';
import { fetchApi } from '../../services/api';
import { useAuth } from '../../store/auth';

interface Reminder {
  id: number;
  title: string;
  kind: string;
  recurrence: string;
}

export default function RemindersScreen() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const router = useRouter();
  
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const loadReminders = async () => {
      if (!user) return;
      try {
        const data = await fetchApi(`/v1/elders/${user.id}/reminders`);
        setReminders(data);
      } catch (e: any) {
        setErrorMsg(e.message || 'I could not connect. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    loadReminders();
  }, [user]);

  return (
    <View style={styles.container}>
      <Text style={styles.title} allowFontScaling={true}>
        {t('myReminders')}
      </Text>

      {errorMsg ? <Text style={styles.error} allowFontScaling={true}>{errorMsg}</Text> : null}

      <ScrollView style={styles.listContainer} contentContainerStyle={{ paddingBottom: theme.spacing.xl }}>
        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.primary} />
        ) : reminders.length === 0 ? (
          <Text style={styles.emptyText} allowFontScaling={true}>
            You have no reminders right now.
          </Text>
        ) : (
          reminders.map((reminder) => (
            <View key={reminder.id} style={styles.card}>
              <Text style={styles.cardTitle} allowFontScaling={true}>
                {reminder.title}
              </Text>
              <Text style={styles.cardSubtitle} allowFontScaling={true}>
                {reminder.recurrence}
              </Text>
            </View>
          ))
        )}
      </ScrollView>

      <BigButton title="Back to Home" onPress={() => router.back()} variant="secondary" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    padding: theme.spacing.xl,
    paddingTop: theme.spacing.xxl * 2,
  },
  title: {
    ...theme.typography.h1,
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  listContainer: {
    flex: 1,
    marginBottom: theme.spacing.lg,
  },
  card: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.lg,
    borderRadius: theme.roundness,
    marginBottom: theme.spacing.md,
  },
  cardTitle: {
    ...theme.typography.h2,
    color: theme.colors.text,
    marginBottom: theme.spacing.xs,
  },
  cardSubtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  emptyText: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginTop: theme.spacing.xl,
  },
  error: {
    ...theme.typography.body,
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  }
});
