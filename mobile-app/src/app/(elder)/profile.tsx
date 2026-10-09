import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { BigButton } from '../../components/BigButton';
import { useAuth } from '../../store/auth';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, signOut } = useAuth();

  return (
    <View style={styles.container}>
      <Text style={styles.title} allowFontScaling={true}>
        My Profile
      </Text>

      <View style={styles.infoCard}>
        <Text style={styles.label} allowFontScaling={true}>Name</Text>
        <Text style={styles.value} allowFontScaling={true}>{user?.full_name}</Text>
        
        <Text style={styles.label} allowFontScaling={true}>Email</Text>
        <Text style={styles.value} allowFontScaling={true}>{user?.email}</Text>
        
        <Text style={styles.label} allowFontScaling={true}>Role</Text>
        <Text style={styles.value} allowFontScaling={true}>{user?.role}</Text>
      </View>

      <View style={styles.buttonContainer}>
        <BigButton title="Sign Out" onPress={signOut} variant="danger" />
        <BigButton title="Back to Home" onPress={() => router.back()} variant="secondary" />
      </View>
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
  infoCard: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.xl,
    borderRadius: theme.roundness,
    marginBottom: theme.spacing.xxl,
  },
  label: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  value: {
    ...theme.typography.h2,
    color: theme.colors.text,
    marginBottom: theme.spacing.lg,
  },
  buttonContainer: {
    gap: theme.spacing.md,
  }
});
