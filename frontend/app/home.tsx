import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Card } from '../components/Card';
import { authStore, UserSession } from '../store/authStore';
import { api } from '../services/api';

export default function HomeScreen() {
  const router = useRouter();
  const [user, setUser] = useState<UserSession | null>(authStore.getUser());
  const [nextReminder, setNextReminder] = useState<string | null>(null);
  const [todayCount, setTodayCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const unsubscribe = authStore.subscribe(() => {
      setUser(authStore.getUser());
    });

    loadRemindersSummary();
    return () => {
      unsubscribe();
    };
  }, []);

  const loadRemindersSummary = async () => {
    const currentUser = authStore.getUser();
    if (!currentUser) return;
    setLoading(true);
    try {
      const activities = await api.getActivities(currentUser.id, 'REMINDER');
      setTodayCount(activities.length);
      const pending = activities.find((a) => a.status === 'PENDING');
      if (pending) {
        setNextReminder(pending.description);
      } else if (activities.length > 0) {
        setNextReminder('All reminders completed for today!');
      } else {
        setNextReminder('No reminders scheduled for today.');
      }
    } catch (err: any) {
      setNextReminder('Tap below to view reminders.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 30 }}>
      {/* Elder Greeting Banner */}
      <View style={styles.header}>
        <Text style={styles.greetingLabel}>Hello,</Text>
        <Text style={styles.elderName}>{user?.fullName || user?.email || 'Friend'}</Text>
      </View>

      {/* Emergency Help Button */}
      <TouchableOpacity
        style={styles.sosButton}
        activeOpacity={0.85}
        onPress={() => router.push('/sos')}
      >
        <Text style={styles.sosText}>🚨 I NEED HELP</Text>
        <Text style={styles.sosSubtext}>Tap for Emergency SOS</Text>
      </TouchableOpacity>

      {/* Talk to AI Button */}
      <TouchableOpacity
        style={styles.aiButton}
        activeOpacity={0.85}
        onPress={() => router.push('/conversation')}
      >
        <Text style={styles.aiButtonText}>🤖 TALK TO OLDY BUDDY</Text>
        <Text style={styles.aiButtonSub}>Ask questions or chat anytime</Text>
      </TouchableOpacity>

      {/* Today's Reminders Card */}
      <Card title="⏰ Today's Reminders" onPress={() => router.push('/reminders')}>
        {loading ? (
          <ActivityIndicator size="small" color="#3730a3" />
        ) : (
          <>
            <Text style={styles.cardHighlight}>Next Reminder:</Text>
            <Text style={styles.reminderDetail}>{nextReminder}</Text>
            <Text style={styles.summaryFooter}>Total Today: {todayCount} reminder(s)</Text>
          </>
        )}
      </Card>

      {/* Profile & Settings Navigation Card */}
      <Card title="👤 My Profile" onPress={() => router.push('/profile')}>
        <Text style={styles.cardDesc}>View your information, preferences, and emergency contact details.</Text>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
  },
  greetingLabel: {
    fontSize: 20,
    color: '#64748b',
    fontWeight: '600',
  },
  elderName: {
    fontSize: 34,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  sosButton: {
    backgroundColor: '#dc2626',
    marginHorizontal: 16,
    marginVertical: 10,
    paddingVertical: 22,
    borderRadius: 20,
    alignItems: 'center',
    elevation: 4,
    borderWidth: 2,
    borderColor: '#991b1b',
  },
  sosText: {
    color: '#ffffff',
    fontSize: 26,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  sosSubtext: {
    color: '#fef2f2',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 4,
  },
  aiButton: {
    backgroundColor: '#3730a3',
    marginHorizontal: 16,
    marginVertical: 8,
    paddingVertical: 20,
    borderRadius: 20,
    alignItems: 'center',
    elevation: 3,
    borderWidth: 2,
    borderColor: '#1e1b4b',
  },
  aiButtonText: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  aiButtonSub: {
    color: '#e0e7ff',
    fontSize: 16,
    marginTop: 4,
  },
  cardHighlight: {
    fontSize: 18,
    fontWeight: '700',
    color: '#334155',
  },
  reminderDetail: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#3730a3',
    marginVertical: 6,
  },
  summaryFooter: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 4,
  },
  cardDesc: {
    fontSize: 18,
    color: '#475569',
  },
});
