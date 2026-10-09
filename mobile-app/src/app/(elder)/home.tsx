import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { theme } from '../../theme';
import { BigButton } from '../../components/BigButton';
import { useAuth } from '../../store/auth';
import { useTranslation } from '../../i18n';

export default function ElderHomeScreen() {
  const { user, signOut } = useAuth();
  const { t } = useTranslation();
  const router = useRouter();
  
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // update every minute
    return () => clearInterval(timer);
  }, []);

  const timeString = currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const dateString = currentTime.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <TouchableOpacity style={styles.profileBtn} onPress={() => router.push('/(elder)/profile')}>
        <Text style={styles.profileBtnText} allowFontScaling={true}>Profile</Text>
      </TouchableOpacity>
      
      <View style={styles.header}>
        <Text style={styles.greeting} allowFontScaling={true}>
          {t('hello')}, {user?.full_name?.split(' ')[0] || 'Friend'}
        </Text>
        <Text style={styles.time} allowFontScaling={true}>{timeString}</Text>
        <Text style={styles.date} allowFontScaling={true}>{dateString}</Text>
      </View>

      <View style={styles.buttonContainer}>
        <BigButton 
          title={t('talkToBuddy')} 
          onPress={() => router.push('/(elder)/buddy')} 
        />
        <BigButton 
          title={t('myReminders')} 
          onPress={() => router.push('/(elder)/reminders')} 
        />
        <BigButton 
          title={t('callFamily')} 
          onPress={() => router.push('/(elder)/family')} 
        />
        <BigButton 
          title="Food & Groceries" 
          onPress={() => router.push('/(elder)/food')} 
        />
        <BigButton 
          title={t('iNeedHelp')} 
          onPress={() => router.push('/(elder)/sos')} 
          variant="danger" 
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background,
    padding: theme.spacing.xl,
    paddingTop: theme.spacing.xxl * 2, // Space for status bar safely
  },
  header: {
    alignItems: 'center',
    marginBottom: theme.spacing.xxl,
    marginTop: theme.spacing.xl, // Space for the absolute profile button
  },
  profileBtn: {
    position: 'absolute',
    top: theme.spacing.lg,
    right: theme.spacing.xl,
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.sm,
    borderRadius: theme.roundness,
    zIndex: 10,
  },
  profileBtnText: {
    ...theme.typography.body,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  greeting: {
    ...theme.typography.h1,
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
    textAlign: 'center',
  },
  time: {
    fontSize: 48,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: theme.spacing.xs,
    textAlign: 'center',
  },
  date: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  buttonContainer: {
    gap: theme.spacing.md,
  },
});
