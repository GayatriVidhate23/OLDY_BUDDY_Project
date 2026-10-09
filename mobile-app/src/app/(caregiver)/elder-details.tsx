import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { theme } from '../../theme';
import { BigButton } from '../../components/BigButton';

export default function ElderDetailsScreen() {
  const { elderId } = useLocalSearchParams<{ elderId: string }>();
  const router = useRouter();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Elder Management</Text>
      <Text style={styles.subtitle}>ID: {elderId}</Text>

      <View style={styles.buttonContainer}>
        <BigButton 
          title="Alerts & SOS Verification" 
          onPress={() => router.push(`/(caregiver)/alerts?elderId=${elderId}`)} 
          variant="danger"
        />
        <BigButton 
          title="Manage Reminders" 
          onPress={() => router.push(`/(caregiver)/reminders?elderId=${elderId}`)} 
        />
        <BigButton 
          title="Food & Grocery Requests" 
          onPress={() => router.push(`/(caregiver)/food?elderId=${elderId}`)} 
        />
        <BigButton 
          title="Emergency Contacts" 
          onPress={() => router.push(`/(caregiver)/contacts?elderId=${elderId}`)} 
        />
      </View>

      <BigButton 
        title="Back to Dashboard" 
        onPress={() => router.back()} 
        variant="secondary"
        style={{ marginTop: theme.spacing.xxl }}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: theme.spacing.xl,
    paddingTop: theme.spacing.xxl * 2,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: theme.spacing.xs,
  },
  subtitle: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.xxl,
  },
  buttonContainer: {
    gap: theme.spacing.lg,
  }
});
