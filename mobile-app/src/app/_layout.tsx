import { Slot } from 'expo-router';
import { AuthProvider } from '../store/auth';
import { I18nProvider } from '../i18n';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <I18nProvider>
        <AuthProvider>
          <Slot />
        </AuthProvider>
      </I18nProvider>
    </SafeAreaProvider>
  );
}
