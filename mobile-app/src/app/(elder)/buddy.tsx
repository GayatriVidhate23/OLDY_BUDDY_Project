import { useState, useRef } from 'react';
import { View, Text, StyleSheet, TextInput, ScrollView } from 'react-native';
import { theme } from '../../theme';
import { useTranslation } from '../../i18n';
import { BigButton } from '../../components/BigButton';
import { fetchApi } from '../../services/api';

type BuddyState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

export default function TalkToBuddyScreen() {
  const { t } = useTranslation();
  
  const [buddyState, setBuddyState] = useState<BuddyState>('IDLE');
  const [replyText, setReplyText] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  
  // Fallback text input state
  const [showKeyboard, setShowKeyboard] = useState(false);
  const [typedText, setTypedText] = useState('');
  
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Stable session ID for the backend
  const sessionId = useRef(`session_${Date.now()}_${Math.random().toString(36).substring(7)}`).current;

  // We are missing expo-av for actual microphone recording, and the /converse endpoint.
  // This logic simulates the UX flow and prepares for the real integration.

  const handleMicTap = () => {
    setErrorMsg('');
    if (buddyState === 'IDLE' || buddyState === 'SPEAKING') {
      // Start recording
      setBuddyState('LISTENING');
      setReplyText('');
      
      // Safety limit: 30 seconds max
      timeoutRef.current = setTimeout(() => {
        handleStopListening();
      }, 30000);
    } else if (buddyState === 'LISTENING') {
      // Stop recording
      handleStopListening();
    }
  };

  const handleStopListening = async () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setBuddyState('THINKING');
    try {
      // Intentionally using the real missing endpoint to report the 404 gap
      const data = await fetchApi('/converse-audio', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, audio_base64: 'placeholder' })
      });
      
      // If it worked:
      setBuddyState('SPEAKING');
      setReplyText(data.reply_text || '...');
    } catch (e: any) {
      setBuddyState('IDLE');
      setErrorMsg(e.message || 'I could not connect. Please try again, or call your family.');
    }
  };

  const handleTextSubmit = async () => {
    if (!typedText.trim()) return;
    setErrorMsg('');
    setShowKeyboard(false);
    setBuddyState('THINKING');
    
    try {
      const data = await fetchApi('/converse', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, text: typedText })
      });
      setTypedText('');
      setBuddyState('SPEAKING');
      setReplyText(data.reply_text || '...');
    } catch (e: any) {
      setBuddyState('IDLE');
      setErrorMsg(e.message || 'I could not connect. Please try again, or call your family.');
    }
  };

  const getStatusText = () => {
    switch (buddyState) {
      case 'LISTENING': return 'I am listening...';
      case 'THINKING': return 'Thinking...';
      case 'SPEAKING': return 'Buddy says:';
      default: return 'Tap the mic to talk to Buddy';
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.status} allowFontScaling={true}>
        {getStatusText()}
      </Text>

      {errorMsg ? <Text style={styles.error} allowFontScaling={true}>{errorMsg}</Text> : null}

      {buddyState === 'SPEAKING' && replyText ? (
        <View style={styles.replyBox}>
          <Text style={styles.replyText} allowFontScaling={true}>{replyText}</Text>
          <BigButton 
            title="Hear again" 
            onPress={() => { /* Play audio again using expo-av */ }} 
            variant="secondary"
          />
        </View>
      ) : null}

      {!showKeyboard && buddyState !== 'THINKING' && (
        <View style={styles.micContainer}>
          <BigButton 
            title={buddyState === 'LISTENING' ? "Stop" : "Talk"} 
            onPress={handleMicTap}
            style={buddyState === 'LISTENING' ? styles.micButtonActive : styles.micButton}
          />
          {buddyState === 'IDLE' && (
            <BigButton 
              title="Type instead" 
              onPress={() => setShowKeyboard(true)} 
              variant="secondary" 
            />
          )}
        </View>
      )}

      {showKeyboard && (
        <View style={styles.keyboardContainer}>
          <TextInput
            style={styles.input}
            placeholder="Type your message..."
            value={typedText}
            onChangeText={setTypedText}
            multiline
            allowFontScaling={true}
          />
          <BigButton title="Send" onPress={handleTextSubmit} />
          <BigButton title="Cancel" onPress={() => setShowKeyboard(false)} variant="secondary" />
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: theme.spacing.xl,
    justifyContent: 'center',
  },
  status: {
    ...theme.typography.h2,
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  micContainer: {
    alignItems: 'center',
    gap: theme.spacing.lg,
  },
  micButton: {
    minHeight: 160,
    width: 160,
    borderRadius: 80,
    backgroundColor: theme.colors.primary,
  },
  micButtonActive: {
    minHeight: 160,
    width: 160,
    borderRadius: 80,
    backgroundColor: theme.colors.error,
  },
  replyBox: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.lg,
    borderRadius: theme.roundness,
    marginBottom: theme.spacing.xl,
  },
  replyText: {
    ...theme.typography.body,
    color: theme.colors.text,
    marginBottom: theme.spacing.lg,
  },
  keyboardContainer: {
    gap: theme.spacing.md,
  },
  input: {
    ...theme.typography.body,
    borderWidth: 2,
    borderColor: theme.colors.border,
    borderRadius: theme.roundness,
    padding: theme.spacing.md,
    minHeight: 120,
    textAlignVertical: 'top',
  },
  error: {
    ...theme.typography.body,
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  }
});
