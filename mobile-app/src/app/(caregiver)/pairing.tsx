import { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { theme } from '../../theme';
import { fetchApi } from '../../services/api';
import { BigButton } from '../../components/BigButton';

export default function CaregiverPairingScreen() {
  const { elderId } = useLocalSearchParams<{ elderId: string }>();
  const router = useRouter();

  const [pairingCode, setPairingCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const generateCode = async () => {
    if (!elderId) return;
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await fetchApi(`/v1/elders/${elderId}/pairing-code`, {
        method: 'POST'
      });
      setPairingCode(data.code);
    } catch (e: any) {
      setErrorMsg(e.message || 'Could not generate code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Generate Pairing Code</Text>
      
      <Text style={styles.description}>
        Give this 6-digit code to the elder so they can log into their device. The code will expire shortly.
      </Text>

      {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}

      <View style={styles.codeContainer}>
        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.primary} />
        ) : pairingCode ? (
          <Text style={styles.codeText}>{pairingCode}</Text>
        ) : (
          <Text style={styles.placeholderText}>No code generated yet</Text>
        )}
      </View>

      <View style={styles.buttonContainer}>
        <BigButton 
          title={pairingCode ? "Generate New Code" : "Generate Code"} 
          onPress={generateCode} 
        />
        <BigButton 
          title="Back to Dashboard" 
          onPress={() => router.back()} 
          variant="secondary"
        />
      </View>
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
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  },
  description: {
    fontSize: 18,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.xxl,
    lineHeight: 26,
  },
  codeContainer: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.xxl,
    borderRadius: theme.roundness,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 160,
    marginBottom: theme.spacing.xxl,
  },
  codeText: {
    fontSize: 64,
    fontWeight: 'bold',
    color: theme.colors.primary,
    letterSpacing: 8,
  },
  placeholderText: {
    fontSize: 20,
    color: theme.colors.textSecondary,
    fontStyle: 'italic',
  },
  error: {
    fontSize: 16,
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  },
  buttonContainer: {
    gap: theme.spacing.md,
  }
});
