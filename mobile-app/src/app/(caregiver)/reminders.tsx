import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TextInput, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { theme } from '../../theme';
import { fetchApi } from '../../services/api';
import { BigButton } from '../../components/BigButton';

export default function CaregiverRemindersScreen() {
  const { elderId } = useLocalSearchParams<{ elderId: string }>();
  const router = useRouter();

  const [reminders, setReminders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  
  const [isAdding, setIsAdding] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newKind, setNewKind] = useState('medicine');
  const [newRecurrence, setNewRecurrence] = useState('daily');

  useEffect(() => {
    loadReminders();
  }, [elderId]);

  const loadReminders = async () => {
    if (!elderId) return;
    setLoading(true);
    try {
      const data = await fetchApi(`/v1/elders/${elderId}/reminders`);
      setReminders(data);
    } catch (e: any) {
      setErrorMsg(e.message || 'Could not load reminders.');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!newTitle.trim()) {
      setErrorMsg('Title cannot be empty');
      return;
    }
    setLoading(true);
    try {
      await fetchApi(`/v1/elders/${elderId}/reminders`, {
        method: 'POST',
        body: JSON.stringify({
          title: newTitle,
          kind: newKind,
          recurrence: newRecurrence,
        })
      });
      setIsAdding(false);
      setNewTitle('');
      await loadReminders();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to add reminder.');
      setLoading(false);
    }
  };

  const handleDelete = async (rid: number) => {
    setLoading(true);
    try {
      await fetchApi(`/v1/elders/${elderId}/reminders/${rid}`, { method: 'DELETE' });
      await loadReminders();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to delete reminder.');
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Manage Reminders</Text>

      {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}

      {isAdding ? (
        <View style={styles.addForm}>
          <Text style={styles.sectionTitle}>New Reminder</Text>
          <TextInput
            style={styles.input}
            placeholder="Reminder Title (e.g., Take Meds)"
            value={newTitle}
            onChangeText={setNewTitle}
          />
          <View style={styles.buttonContainer}>
            <BigButton title="Save" onPress={handleAdd} style={{ flex: 1 }} />
            <BigButton title="Cancel" onPress={() => setIsAdding(false)} variant="secondary" style={{ flex: 1 }} />
          </View>
        </View>
      ) : (
        <BigButton 
          title="Add New Reminder" 
          onPress={() => setIsAdding(true)} 
          style={{ marginBottom: theme.spacing.xl }} 
        />
      )}

      {loading ? (
        <ActivityIndicator size="large" color={theme.colors.primary} style={{ marginTop: 40 }} />
      ) : reminders.length === 0 ? (
        <Text style={styles.emptyText}>No reminders set for this elder.</Text>
      ) : (
        reminders.map((rem) => (
          <View key={rem.id} style={styles.card}>
            <View style={{ flex: 1 }}>
              <Text style={styles.cardTitle}>{rem.title}</Text>
              <Text style={styles.subtitle}>{rem.recurrence}</Text>
            </View>
            <TouchableOpacity onPress={() => handleDelete(rem.id)} style={styles.deleteBtn}>
              <Text style={styles.deleteBtnText}>Delete</Text>
            </TouchableOpacity>
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
    color: theme.colors.text,
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
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    padding: theme.spacing.lg,
    borderRadius: theme.roundness,
    marginBottom: theme.spacing.lg,
    elevation: 2,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  subtitle: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  deleteBtn: {
    backgroundColor: theme.colors.error,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    borderRadius: theme.roundness,
  },
  deleteBtnText: {
    color: theme.colors.background,
    fontWeight: 'bold',
  },
  addForm: {
    backgroundColor: theme.colors.background,
    padding: theme.spacing.xl,
    borderRadius: theme.roundness,
    marginBottom: theme.spacing.xl,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: theme.spacing.md,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.roundness,
    padding: theme.spacing.md,
    fontSize: 18,
    marginBottom: theme.spacing.lg,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  }
});
