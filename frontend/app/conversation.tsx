import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { api } from '../services/api';
import { authStore } from '../store/authStore';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
}

export default function ConversationScreen() {
  const user = authStore.getUser();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: '1', sender: 'ai', text: 'Hello! I am your Oldy Buddy assistant. How can I help you today?' },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const sendMessage = async (textToSend: string) => {
    if (!textToSend.trim()) return;

    const userMsg: ChatMessage = { id: Date.now().toString(), sender: 'user', text: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const res = await api.sendChatMessage(textToSend, user?.id);
      const aiMsg: ChatMessage = { id: (Date.now() + 1).toString(), sender: 'ai', text: res.reply };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      Alert.alert('Notice', err.message || 'Could not send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMicPress = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }
    setIsListening(true);
    setTimeout(() => {
      setIsListening(false);
      setInputText('Hello Oldy Buddy, please check my daily medicine');
    }, 2500);
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingVertical: 12 }}
        renderItem={({ item }: { item: ChatMessage }) => {
          const isUser = item.sender === 'user';
          return (
            <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.aiBubble]}>
              <Text style={styles.senderLabel}>{isUser ? 'YOU' : 'OLDY BUDDY'}</Text>
              <Text style={[styles.messageText, isUser ? styles.userText : styles.aiText]}>
                {item.text}
              </Text>
            </View>
          );
        }}
      />

      {loading ? (
        <View style={styles.loadingBox}>
          <ActivityIndicator size="small" color="#3730a3" />
          <Text style={styles.loadingText}>Oldy Buddy is thinking...</Text>
        </View>
      ) : null}

      <View style={styles.inputBar}>
        <TouchableOpacity
          style={[styles.micBtn, isListening && styles.micBtnListening]}
          onPress={handleMicPress}
          activeOpacity={0.8}
        >
          <Text style={styles.micBtnText}>{isListening ? '🎙️ LISTENING...' : '🎤 VOICE'}</Text>
        </TouchableOpacity>

        <TextInput
          style={styles.textInput}
          placeholder="Type or tap voice..."
          placeholderTextColor="#94a3b8"
          value={inputText}
          onChangeText={setInputText}
        />

        <TouchableOpacity
          style={styles.sendBtn}
          onPress={() => sendMessage(inputText)}
          disabled={loading || !inputText.trim()}
          activeOpacity={0.8}
        >
          <Text style={styles.sendBtnText}>SEND</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
    padding: 12,
  },
  messageBubble: {
    padding: 18,
    borderRadius: 18,
    marginVertical: 6,
    maxWidth: '86%',
    borderWidth: 2,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#3730a3',
    borderColor: '#1e1b4b',
  },
  aiBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#ffffff',
    borderColor: '#cbd5e1',
  },
  senderLabel: {
    fontSize: 14,
    fontWeight: '800',
    color: '#94a3b8',
    marginBottom: 4,
  },
  messageText: {
    fontSize: 20,
    lineHeight: 28,
    fontWeight: '600',
  },
  userText: {
    color: '#ffffff',
  },
  aiText: {
    color: '#0f172a',
  },
  loadingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#3730a3',
    marginLeft: 8,
    fontWeight: 'bold',
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderTopWidth: 2,
    borderTopColor: '#e2e8f0',
    backgroundColor: '#ffffff',
    paddingHorizontal: 8,
    borderRadius: 16,
  },
  micBtn: {
    backgroundColor: '#e0e7ff',
    borderWidth: 2,
    borderColor: '#3730a3',
    paddingVertical: 14,
    paddingHorizontal: 12,
    borderRadius: 14,
    marginRight: 6,
  },
  micBtnListening: {
    backgroundColor: '#fef2f2',
    borderColor: '#dc2626',
  },
  micBtnText: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#3730a3',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#f1f5f9',
    borderWidth: 2,
    borderColor: '#cbd5e1',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 18,
    color: '#0f172a',
  },
  sendBtn: {
    backgroundColor: '#3730a3',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 14,
    marginLeft: 6,
  },
  sendBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
