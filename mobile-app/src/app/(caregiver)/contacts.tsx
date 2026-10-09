import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TextInput, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { theme } from '../../theme';
import { fetchApi } from '../../services/api';
import { BigButton } from '../../components/BigButton';

export default function CaregiverContactsScreen() {
  const { elderId } = useLocalSearchParams<{ elderId: string }>();
  const router = useRouter();

  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState('');
  const [newPhone, setNewPhone] = useState('');

  useEffect(() => {
    loadContacts();
  }, [elderId]);

  const loadContacts = async () => {
    if (!elderId) return;
    setLoading(true);
    try {
      const data = await fetchApi(`/v1/elders/${elderId}/emergency-contacts`);
      setContacts(data);
    } catch (e: any) {
      setErrorMsg(e.message || 'Could not load contacts.');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!newName.trim() || !newPhone.trim()) {
      setErrorMsg('Name and Phone are required');
      return;
    }
    setLoading(true);
    try {
      await fetchApi(`/v1/elders/${elderId}/emergency-contacts`, {
        method: 'POST',
        body: JSON.stringify({
          name: newName,
          phone_e164: newPhone,
        })
      });
      setIsAdding(false);
      setNewName('');
      setNewPhone('');
      await loadContacts();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to add contact (Max 5 allowed).');
      setLoading(false);
    }
  };

  const handleDelete = async (cid: number) => {
    setLoading(true);
    try {
      await fetchApi(`/v1/elders/${elderId}/emergency-contacts/${cid}`, { method: 'DELETE' });
      await loadContacts();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to delete contact.');
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Emergency Contacts</Text>

      {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}

      {isAdding ? (
        <View style={styles.addForm}>
          <Text style={styles.sectionTitle}>New Contact</Text>
          <TextInput
            style={styles.input}
            placeholder="Name (e.g., Son)"
            value={newName}
            onChangeText={setNewName}
          />
          <TextInput
            style={styles.input}
            placeholder="Phone (e.g., +1234567890)"
            value={newPhone}
            onChangeText={setNewPhone}
            keyboardType="phone-pad"
          />
          <View style={styles.buttonContainer}>
            <BigButton title="Save" onPress={handleAdd} style={{ flex: 1 }} />
            <BigButton title="Cancel" onPress={() => setIsAdding(false)} variant="secondary" style={{ flex: 1 }} />
          </View>
        </View>
      ) : (
        <BigButton 
          title="Add New Contact" 
          onPress={() => setIsAdding(true)} 
          style={{ marginBottom: theme.spacing.xl }} 
        />
      )}

      {loading ? (
        <ActivityIndicator size="large" color={theme.colors.primary} style={{ marginTop: 40 }} />
      ) : contacts.length === 0 ? (
        <Text style={styles.emptyText}>No emergency contacts set.</Text>
      ) : (
        contacts.map((contact) => (
          <View key={contact.id} style={styles.card}>
            <View style={{ flex: 1 }}>
              <Text style={styles.cardTitle}>{contact.name}</Text>
              <Text style={styles.subtitle}>{contact.phone_e164}</Text>
            </View>
            <TouchableOpacity onPress={() => handleDelete(contact.id)} style={styles.deleteBtn}>
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
