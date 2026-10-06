import { useState } from 'react';
import { View, Text, TextInput, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { useStore } from '../store/store';
import { apiClient } from '../services/api';
import { LargeButton } from '../components/LargeButton';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';

export default function Chat() {
  const userId = useStore((state: any) => state.userId);
  const [messages, setMessages] = useState([{ role: 'ai', text: 'Hello! I am Buddy. How are you feeling today?' }]);
  const [input, setInput] = useState('');

  const chatMutation = useMutation({
    mutationFn: async (msg: string) => (await apiClient.post(`/elders/${userId}/chat`, { message: msg })).data,
    onSuccess: (data) => {
      setMessages(prev => [...prev, { role: 'ai', text: data.reply }]);
    }
  });

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { role: 'user', text: input }]);
    chatMutation.mutate(input);
    setInput('');
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>Buddy Chat</Text>
        <LargeButton title="Back" variant="dark" onPress={() => router.replace('/home')} />
      </View>
      
      <ScrollView style={styles.chatArea}>
        {messages.map((m, i) => (
          <View key={i} style={[styles.bubble, m.role === 'ai' ? styles.aiBubble : styles.userBubble]}>
            <Text style={[styles.bubbleText, m.role === 'ai' ? styles.aiText : styles.userText]}>{m.text}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={styles.inputArea}>
        <TextInput 
          style={styles.input} 
          value={input} 
          onChangeText={setInput} 
          placeholder="Type a message..." 
          placeholderTextColor="#9ca3af"
        />
        <LargeButton title="Send" variant="lime" onPress={handleSend} />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  header: { padding: 24, paddingTop: 60, backgroundColor: '#0ea5e9', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerText: { fontSize: 32, fontWeight: '800', color: '#ffffff' },
  chatArea: { flex: 1, padding: 24 },
  bubble: { padding: 16, borderRadius: 20, marginBottom: 16, maxWidth: '85%' },
  aiBubble: { backgroundColor: '#ffffff', alignSelf: 'flex-start', borderBottomLeftRadius: 4 },
  userBubble: { backgroundColor: '#111827', alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  bubbleText: { fontSize: 20, fontWeight: '500' },
  aiText: { color: '#111827' },
  userText: { color: '#ffffff' },
  inputArea: { padding: 24, backgroundColor: '#ffffff', borderTopWidth: 1, borderColor: '#e5e7eb' },
  input: { backgroundColor: '#f3f4f6', padding: 20, borderRadius: 16, fontSize: 20, marginBottom: 12, color: '#111827' }
});
