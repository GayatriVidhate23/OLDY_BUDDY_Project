import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { api } from '../services/api';
import { authStore } from '../store/authStore';

export default function LoginScreen() {
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'ELDER' | 'CAREGIVER' | 'FAMILY'>('ELDER');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Missing Info', 'Please enter both your email address and password.');
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        await api.register(email.trim(), password.trim(), role, fullName.trim());
      }

      const tokenRes = await api.login(email.trim(), password.trim());
      authStore.setUser({ id: 0, email: email.trim(), role }, tokenRes.access_token);

      // Fetch verified user session from backend
      const me = await api.getMe();
      authStore.setUser(
        {
          id: me.id,
          email: me.email,
          fullName: me.full_name,
          role: me.role as any,
        },
        tokenRes.access_token
      );

      router.replace('/home');
    } catch (err: any) {
      Alert.alert('Login Failed', err.message || 'Incorrect email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>{isRegister ? 'Create Account' : 'Welcome Back'}</Text>
      <Text style={styles.subtitle}>Oldy Buddy Elder Care Companion</Text>

      {isRegister ? (
        <>
          <Text style={styles.label}>Your Full Name</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Mary Smith"
            placeholderTextColor="#94a3b8"
            value={fullName}
            onChangeText={setFullName}
          />

          <Text style={styles.label}>I am a:</Text>
          <View style={styles.roleContainer}>
            {(['ELDER', 'CAREGIVER', 'FAMILY'] as const).map((r) => (
              <TouchableOpacity
                key={r}
                style={[styles.roleBtn, role === r && styles.roleBtnActive]}
                onPress={() => setRole(r)}
              >
                <Text style={[styles.roleText, role === r && styles.roleTextActive]}>{r}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </>
      ) : null}

      <Text style={styles.label}>Email Address</Text>
      <TextInput
        style={styles.input}
        placeholder="elder@example.com"
        placeholderTextColor="#94a3b8"
        keyboardType="email-address"
        autoCapitalize="none"
        value={email}
        onChangeText={setEmail}
      />

      <Text style={styles.label}>Password</Text>
      <TextInput
        style={styles.input}
        placeholder="••••••••"
        placeholderTextColor="#94a3b8"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      <TouchableOpacity
        style={styles.submitBtn}
        onPress={handleSubmit}
        disabled={loading}
        activeOpacity={0.85}
      >
        {loading ? (
          <ActivityIndicator color="#ffffff" size="large" />
        ) : (
          <Text style={styles.submitText}>{isRegister ? 'REGISTER NOW' : 'SIGN IN'}</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity onPress={() => setIsRegister(!isRegister)} style={styles.switchBtn}>
        <Text style={styles.switchText}>
          {isRegister ? 'Already have an account? Tap to Sign In' : "Need an account? Tap to Register"}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    backgroundColor: '#f8fafc',
    flexGrow: 1,
    justifyContent: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1e1b4b',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 20,
    color: '#475569',
    textAlign: 'center',
    marginBottom: 28,
    marginTop: 6,
  },
  label: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#ffffff',
    borderWidth: 2,
    borderColor: '#cbd5e1',
    borderRadius: 14,
    padding: 18,
    fontSize: 20,
    color: '#0f172a',
  },
  roleContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  roleBtn: {
    flex: 1,
    paddingVertical: 14,
    marginHorizontal: 4,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#cbd5e1',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  roleBtnActive: {
    backgroundColor: '#3730a3',
    borderColor: '#3730a3',
  },
  roleText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#475569',
  },
  roleTextActive: {
    color: '#ffffff',
  },
  submitBtn: {
    backgroundColor: '#3730a3',
    paddingVertical: 20,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 28,
    elevation: 3,
  },
  submitText: {
    color: '#ffffff',
    fontSize: 22,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  switchBtn: {
    marginTop: 24,
    alignItems: 'center',
    padding: 10,
  },
  switchText: {
    color: '#3730a3',
    fontSize: 18,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
});
