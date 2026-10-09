import { useState } from 'react';
import { View, Text, TextInput, StyleSheet, ActivityIndicator } from 'react-native';
import { theme } from '../../theme';
import { useTranslation } from '../../i18n';
import { BigButton } from '../../components/BigButton';
import { useAuth } from '../../store/auth';
import { fetchApi } from '../../services/api';
import { useRouter } from 'expo-router';

export default function LoginScreen() {
  const { t } = useTranslation();
  const { signIn } = useAuth();
  const router = useRouter();

  const [roleMode, setRoleMode] = useState<'NONE' | 'ELDER' | 'CAREGIVER'>('NONE');
  const [pairingCode, setPairingCode] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleElderLogin = async () => {
    setErrorMsg('');
    if (pairingCode.length !== 6) {
      setErrorMsg('Code must be 6 digits.');
      return;
    }
    setLoading(true);
    try {
      const data = await fetchApi('/v1/auth/pair', {
        method: 'POST',
        body: JSON.stringify({ code: pairingCode }),
      });
      await signIn(data.access_token, data.refresh_token);
      // Redirection handled by auth guard
    } catch (e: any) {
      setErrorMsg(e.message || 'I could not connect. Please try again, or call your family.');
    } finally {
      setLoading(false);
    }
  };

  const handleCaregiverLogin = async () => {
    setErrorMsg('');
    if (!email || !password) {
      setErrorMsg('Please enter email and password.');
      return;
    }
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const data = await fetchApi('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });
      await signIn(data.access_token, data.refresh_token);
    } catch (e: any) {
      setErrorMsg(e.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  if (roleMode === 'NONE') {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>{t('login')}</Text>
        <BigButton 
          title="I am an Elder" 
          onPress={() => setRoleMode('ELDER')} 
        />
        <BigButton 
          title="I am a Caregiver" 
          onPress={() => setRoleMode('CAREGIVER')} 
          variant="secondary"
        />
        <BigButton 
          title="Change Language" 
          onPress={() => router.replace('/(auth)/language')} 
          variant="secondary"
        />
      </View>
    );
  }

  if (roleMode === 'ELDER') {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Enter your code</Text>
        {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}
        
        <TextInput
          style={styles.input}
          placeholder="6-digit code"
          value={pairingCode}
          onChangeText={setPairingCode}
          keyboardType="number-pad"
          maxLength={6}
          editable={!loading}
          allowFontScaling={true}
        />
        
        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.primary} style={styles.loader} />
        ) : (
          <>
            <BigButton title="Submit" onPress={handleElderLogin} />
            <BigButton title="Back" onPress={() => setRoleMode('NONE')} variant="secondary" />
          </>
        )}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Caregiver Login</Text>
      {errorMsg ? <Text style={styles.errorCaregiver}>{errorMsg}</Text> : null}
      
      <TextInput
        style={styles.inputCaregiver}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
        editable={!loading}
        allowFontScaling={true}
      />
      <TextInput
        style={styles.inputCaregiver}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        editable={!loading}
        allowFontScaling={true}
      />
      
      {loading ? (
        <ActivityIndicator size="large" color={theme.colors.primary} style={styles.loader} />
      ) : (
        <>
          <BigButton title="Login" onPress={handleCaregiverLogin} />
          <BigButton title="Back" onPress={() => setRoleMode('NONE')} variant="secondary" />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    justifyContent: 'center',
    padding: theme.spacing.lg,
  },
  title: {
    ...theme.typography.h1,
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  input: {
    ...theme.typography.h1,
    borderWidth: 2,
    borderColor: theme.colors.border,
    borderRadius: theme.roundness,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.xl,
    textAlign: 'center',
    letterSpacing: 8,
  },
  inputCaregiver: {
    ...theme.typography.body,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.roundness,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  error: {
    ...theme.typography.body,
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  },
  errorCaregiver: {
    ...theme.typography.caption,
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.md,
  },
  loader: {
    marginVertical: theme.spacing.xl,
  }
});
