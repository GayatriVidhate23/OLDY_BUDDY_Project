import { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';
import { theme } from '../../theme';
import { BigButton } from '../../components/BigButton';
import { fetchApi } from '../../services/api';
import { useAuth } from '../../store/auth';

export default function ConsentScreen() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleAgree = async () => {
    if (!user) return;
    setLoading(true);
    setErrorMsg('');
    try {
      await fetchApi(`/v1/elders/${user.id}/consents`, {
        method: 'POST',
        body: JSON.stringify({ kind: 'voice_call' }),
      });
      await SecureStore.setItemAsync('has_consented', 'true');
      router.replace('/(elder)/home');
    } catch (e: any) {
      setErrorMsg(e.message || 'Could not save your choice. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecline = () => {
    // If they decline, they can't use the app.
    signOut();
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title} allowFontScaling={true}>
        Welcome to Oldy Buddy!
      </Text>
      <Text style={styles.bodyText} allowFontScaling={true}>
        Before we begin, we need your permission to use voice calls and send alerts to your family if you need help.
      </Text>
      
      {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}
      
      {loading ? (
        <ActivityIndicator size="large" color={theme.colors.primary} style={{ margin: theme.spacing.xl }} />
      ) : (
        <View style={styles.buttonContainer}>
          <BigButton title="Yes, I Agree" onPress={handleAgree} />
          <BigButton title="No, Sign Out" onPress={handleDecline} variant="secondary" />
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    justifyContent: 'center',
    padding: theme.spacing.xl,
  },
  title: {
    ...theme.typography.h1,
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  },
  bodyText: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.xxl,
  },
  buttonContainer: {
    gap: theme.spacing.md,
  },
  error: {
    ...theme.typography.body,
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  }
});
