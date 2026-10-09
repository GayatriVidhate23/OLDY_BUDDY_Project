import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { useTranslation } from '../../i18n';
import { BigButton } from '../../components/BigButton';

export default function LanguageScreen() {
  const { setLang } = useTranslation();
  const router = useRouter();

  const handleSelectLanguage = async (lang: 'en' | 'hi' | 'mr') => {
    await setLang(lang);
    router.replace('/(auth)/login');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Choose Language</Text>
      
      <View style={styles.buttonContainer}>
        <BigButton 
          title="English" 
          onPress={() => handleSelectLanguage('en')} 
          variant="secondary"
        />
        <BigButton 
          title="हिन्दी" 
          onPress={() => handleSelectLanguage('hi')} 
          variant="secondary"
        />
        <BigButton 
          title="मराठी" 
          onPress={() => handleSelectLanguage('mr')} 
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
    justifyContent: 'center',
    padding: theme.spacing.lg,
  },
  title: {
    ...theme.typography.h1,
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.xxl,
  },
  buttonContainer: {
    gap: theme.spacing.md,
  },
});
