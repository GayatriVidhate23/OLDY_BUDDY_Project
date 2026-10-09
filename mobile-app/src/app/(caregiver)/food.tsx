import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { BigButton } from '../../components/BigButton';

export default function CaregiverFoodScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Food & Groceries</Text>
      
      <View style={styles.stubContainer}>
        <Text style={styles.stubText}>
          This feature is coming soon! Soon you will be able to manage grocery requests from the elder here.
        </Text>
      </View>

      <BigButton title="Back" onPress={() => router.back()} variant="secondary" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.xl,
    paddingTop: theme.spacing.xxl * 2,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
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
    fontSize: 20,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 34,
  }
});
