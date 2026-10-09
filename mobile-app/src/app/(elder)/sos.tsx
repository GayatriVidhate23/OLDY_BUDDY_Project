import { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { BigButton } from '../../components/BigButton';
import { fetchApi } from '../../services/api';

type SOSState = 'CONFIRM' | 'SENDING' | 'SUCCESS' | 'ERROR';

export default function SOSScreen() {
  const router = useRouter();
  
  const [sosState, setSosState] = useState<SOSState>('CONFIRM');
  const [errorMsg, setErrorMsg] = useState('');

  const handleConfirm = async () => {
    setSosState('SENDING');
    setErrorMsg('');
    try {
      await fetchApi('/v1/sos', {
        method: 'POST',
      });
      // Important Safety Rule: Only claim success if backend confirms it.
      setSosState('SUCCESS');
    } catch (e: any) {
      setSosState('ERROR');
      setErrorMsg('I could not connect. Please try again, or call your family.');
    }
  };

  const renderContent = () => {
    switch (sosState) {
      case 'CONFIRM':
        return (
          <>
            <Text style={styles.title} allowFontScaling={true}>
              Do you need help right now?
            </Text>
            <View style={styles.buttonContainer}>
              <BigButton 
                title="YES, I Need Help" 
                onPress={handleConfirm}
                style={styles.confirmButton}
                textStyle={{ fontSize: 32 }}
              />
              <BigButton 
                title="Cancel" 
                onPress={() => router.back()} 
                variant="secondary"
              />
            </View>
          </>
        );
      
      case 'SENDING':
        return (
          <>
            <Text style={styles.title} allowFontScaling={true}>
              Calling for help...
            </Text>
            <ActivityIndicator size="large" color={theme.colors.background} style={{ marginTop: 40 }} />
          </>
        );

      case 'SUCCESS':
        return (
          <>
            <Text style={styles.title} allowFontScaling={true}>
              Help is on the way.
            </Text>
            <Text style={styles.subtitle} allowFontScaling={true}>
              We have alerted your family. Please stay calm.
            </Text>
            <BigButton 
              title="Back to Home" 
              onPress={() => router.back()} 
              variant="secondary"
              style={{ marginTop: 40 }}
            />
          </>
        );

      case 'ERROR':
        return (
          <>
            <Text style={styles.title} allowFontScaling={true}>
              {errorMsg}
            </Text>
            <View style={styles.buttonContainer}>
              <BigButton 
                title="Try Again" 
                onPress={handleConfirm}
                style={styles.confirmButton}
              />
              <BigButton 
                title="Call Family Instead" 
                onPress={() => router.replace('/(elder)/family')}
                variant="secondary"
              />
              <BigButton 
                title="Back" 
                onPress={() => router.back()} 
                variant="secondary"
              />
            </View>
          </>
        );
    }
  };

  return (
    <View style={styles.container}>
      {renderContent()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.error, // Full-screen red background
    justifyContent: 'center',
    padding: theme.spacing.xl,
  },
  title: {
    ...theme.typography.h1,
    color: theme.colors.background, // White text on red
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.background,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  buttonContainer: {
    gap: theme.spacing.lg,
    marginTop: theme.spacing.xl,
  },
  confirmButton: {
    backgroundColor: '#990000', // Darker red for contrast against the background
    minHeight: 120, // Extra huge for panic situations
  }
});
