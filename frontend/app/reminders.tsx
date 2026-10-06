import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { api } from '../services/api';
import { authStore } from '../store/authStore';

const CATEGORIES = [
  { label: '💊 Medication', value: 'Medication: ' },
  { label: '🥤 Meal / Hydration', value: 'Meal: ' },
  { label: '📅 Appointment', value: 'Appointment: ' },
];

export default function RemindersScreen() {
  const user = authStore.getUser();
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadActivities = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await api.getActivities(user.id, 'REMINDER');
      setActivities(data);
    } catch (err: any) {
      Alert.alert('Notice', err.message || 'Could not load reminders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, []);

  const handleAddPreset = async (categoryPrefix: string) => {
    if (!user) return;
    const desc = `${categoryPrefix}${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    try {
      await api.createActivity(user.id, {
        activity_type: 'REMINDER',
        description: desc,
        status: 'PENDING',
      });
      loadActivities();
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to add reminder.');
    }
  };

  const handleToggleComplete = async (item: any) => {
    const newStatus = item.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      await api.updateActivityStatus(item.id, newStatus);
      loadActivities();
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Could not update reminder status.');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.headerTitle}>My Reminders</Text>

      {/* Quick Add Buttons for Elderly */}
      <Text style={styles.sectionLabel}>Quick Add New Reminder:</Text>
      <View style={styles.quickAddRow}>
        {CATEGORIES.map((cat) => (
          <TouchableOpacity
            key={cat.label}
            style={styles.quickAddBtn}
            activeOpacity={0.8}
            onPress={() => handleAddPreset(cat.value)}
          >
            <Text style={styles.quickAddText}>+ {cat.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.sectionLabel}>Today's Schedule:</Text>

      {loading ? (
        <ActivityIndicator size="large" color="#3730a3" style={{ marginTop: 30 }} />
      ) : (
        <FlatList
          data={activities}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={{ paddingBottom: 20 }}
          renderItem={({ item }: { item: any }) => {
            const isDone = item.status === 'COMPLETED';
            return (
              <View style={[styles.reminderCard, isDone && styles.cardDone]}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.reminderDesc, isDone && styles.textDone]}>
                    {item.description}
                  </Text>
                  <Text style={styles.reminderTime}>
                    {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Text>
                </View>

                <TouchableOpacity
                  style={[styles.doneBtn, isDone ? styles.doneBtnActive : styles.doneBtnPending]}
                  onPress={() => handleToggleComplete(item)}
                  activeOpacity={0.8}
                >
                  <Text style={[styles.doneBtnText, isDone && styles.doneBtnTextActive]}>
                    {isDone ? '✓ DONE' : 'MARK DONE'}
                  </Text>
                </TouchableOpacity>
              </View>
            );
          }}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyTitle}>No reminders yet today!</Text>
              <Text style={styles.emptySub}>Tap one of the quick add buttons above to create a reminder.</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
    padding: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0f172a',
    marginBottom: 12,
  },
  sectionLabel: {
    fontSize: 18,
    fontWeight: '700',
    color: '#334155',
    marginVertical: 8,
  },
  quickAddRow: {
    flexDirection: 'column',
    marginBottom: 16,
  },
  quickAddBtn: {
    backgroundColor: '#e0e7ff',
    borderWidth: 2,
    borderColor: '#3730a3',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 14,
    marginVertical: 4,
  },
  quickAddText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#3730a3',
  },
  reminderCard: {
    backgroundColor: '#ffffff',
    padding: 18,
    borderRadius: 16,
    marginVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#cbd5e1',
  },
  cardDone: {
    backgroundColor: '#f1f5f9',
    borderColor: '#cbd5e1',
  },
  reminderDesc: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  textDone: {
    textDecorationLine: 'line-through',
    color: '#64748b',
  },
  reminderTime: {
    fontSize: 15,
    color: '#64748b',
    marginTop: 4,
  },
  doneBtn: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 2,
    marginLeft: 10,
  },
  doneBtnPending: {
    backgroundColor: '#ffffff',
    borderColor: '#16a34a',
  },
  doneBtnActive: {
    backgroundColor: '#16a34a',
    borderColor: '#16a34a',
  },
  doneBtnText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#16a34a',
  },
  doneBtnTextActive: {
    color: '#ffffff',
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 40,
    paddingHorizontal: 20,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#475569',
  },
  emptySub: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    marginTop: 8,
  },
});
