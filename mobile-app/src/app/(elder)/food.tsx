import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { BigButton } from '../../components/BigButton';

export default function FoodScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <Text style={styles.title} allowFontScaling={true}>
        Food & Groceries
      </Text>
      
      <View style={styles.stubContainer}>
        <Text style={styles.stubText} allowFontScaling={true}>
          This feature is coming soon! Soon you will be able to ask your family for groceries directly from here.
        </Text>
      </View>

      <BigButton title="Back to Home" onPress={() => router.back()} variant="secondary" />
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
    ...theme.typography.h1,
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  stubContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stubText: {
    ...theme.typography.h2,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 34,
  }
});
