import { useState } from 'react';
import { View, Text, TextInput, Alert, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import { useStore } from '../store/store';
import { apiClient } from '../services/api';
import { LargeButton } from '../components/LargeButton';
import { jwtDecode } from 'jwt-decode';

export default function Login() {
  const [email, setEmail] = useState('sunita@oldybuddy.com');
  const [password, setPassword] = useState('elder');
  const setAuth = useStore((state: any) => state.setAuth);

  const handleLogin = async () => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const res = await apiClient.post('/auth/login', formData, { headers: { 'Content-Type': 'multipart/form-data' }});
      const token = res.data.access_token;
      const decoded: any = jwtDecode(token);
      
      await setAuth(token, parseInt(decoded.sub));
      router.replace('/home');
    } catch (err: any) {
      Alert.alert("Login Failed", err.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Oldy Buddy</Text>
      <View style={styles.card}>
        <TextInput style={styles.input} value={email} onChangeText={setEmail} placeholder="Email" autoCapitalize="none"/>
        <TextInput style={styles.input} value={password} onChangeText={setPassword} placeholder="Password" secureTextEntry/>
        <LargeButton title="Log In" variant="lime" onPress={handleLogin} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: 'center', backgroundColor: '#0ea5e9' },
  title: { fontSize: 48, fontWeight: '800', marginBottom: 48, textAlign: 'center', color: '#ffffff' },
  card: { backgroundColor: '#ffffff', padding: 32, borderRadius: 32, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 16 },
  input: { padding: 24, borderRadius: 16, fontSize: 24, marginBottom: 24, borderWidth: 1, borderColor: '#e5e7eb', backgroundColor: '#f9fafb' }
});
