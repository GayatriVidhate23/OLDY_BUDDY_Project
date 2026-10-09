import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import * as Linking from 'expo-linking';
import { theme } from '../../theme';
import { useTranslation } from '../../i18n';
import { BigButton } from '../../components/BigButton';
import { fetchApi } from '../../services/api';
import { useAuth } from '../../store/auth';

interface Contact {
  id: number;
  name: string;
  phone_e164: string;
}

export default function FamilyScreen() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const router = useRouter();
  
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const loadContacts = async () => {
      if (!user) return;
      try {
        const data = await fetchApi(`/v1/elders/${user.id}/emergency-contacts`);
        setContacts(data);
      } catch (e: any) {
        setErrorMsg(e.message || 'I could not connect. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    loadContacts();
  }, [user]);

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`).catch(() => {
      setErrorMsg('Could not open the phone dialer. Please try again.');
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title} allowFontScaling={true}>
        {t('callFamily')}
      </Text>

      {errorMsg ? <Text style={styles.error} allowFontScaling={true}>{errorMsg}</Text> : null}

      <ScrollView style={styles.listContainer} contentContainerStyle={{ paddingBottom: theme.spacing.xl }}>
        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.primary} />
        ) : contacts.length === 0 ? (
          <Text style={styles.emptyText} allowFontScaling={true}>
            No family contacts found.
          </Text>
        ) : (
          contacts.map((contact) => (
            <BigButton 
              key={contact.id} 
              title={`Call ${contact.name}`} 
              onPress={() => handleCall(contact.phone_e164)} 
            />
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
