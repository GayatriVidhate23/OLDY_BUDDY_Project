import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { api } from '../services/api';
import { authStore } from '../store/authStore';

export default function ProfileScreen() {
  const router = useRouter();
  const user = authStore.getUser();

  const [emergencyContact, setEmergencyContact] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('English');
  const [medicalNotes, setMedicalNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    api.getElderProfile(user.id)
      .then((data) => {
        setEmergencyContact(data.emergency_contact || '');
        if (data.preferences?.language) {
          setPreferredLanguage(data.preferences.language);
        }
        if (data.medical_info?.notes) {
          setMedicalNotes(data.medical_info.notes);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await api.updateElderProfile(user.id, {
        emergency_contact: emergencyContact,
        preferences: { language: preferredLanguage },
        medical_info: { notes: medicalNotes },
      });
      Alert.alert('Saved', 'Your profile details have been updated!');
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Could not save profile details.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    authStore.logout();
    router.replace('/login');
  };

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>My Profile & Settings</Text>

      {/* Account Info Box */}
      <View style={styles.infoCard}>
        <Text style={styles.infoLabel}>Account Name:</Text>
        <Text style={styles.infoValue}>{user?.fullName || user?.email || 'N/A'}</Text>
        <Text style={styles.infoLabel}>Role & Email:</Text>
        <Text style={styles.infoValueSub}>{user?.role} • {user?.email}</Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color="#3730a3" style={{ marginVertical: 20 }} />
      ) : (
        <>
          <Text style={styles.fieldLabel}>Emergency Contact Phone:</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. +1 555-019-2834"
            placeholderTextColor="#94a3b8"
            keyboardType="phone-pad"
            value={emergencyContact}
            onChangeText={setEmergencyContact}
          />

          <Text style={styles.fieldLabel}>Preferred Language:</Text>
          <View style={styles.langRow}>
            {['English', 'Spanish', 'French'].map((lang) => (
              <TouchableOpacity
                key={lang}
                style={[styles.langBtn, preferredLanguage === lang && styles.langBtnActive]}
                onPress={() => setPreferredLanguage(lang)}
              >
                <Text style={[styles.langText, preferredLanguage === lang && styles.langTextActive]}>
                  {lang}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.fieldLabel}>Basic Medical Notes:</Text>
          <TextInput
            style={[styles.input, { height: 110 }]}
            placeholder="e.g. High blood pressure, takes morning medication"
            placeholderTextColor="#94a3b8"
            multiline
            value={medicalNotes}
            onChangeText={setMedicalNotes}
          />

          <TouchableOpacity style={styles.saveBtn} onPress={handleSave} disabled={saving} activeOpacity={0.85}>
            <Text style={styles.saveBtnText}>{saving ? 'SAVING...' : 'SAVE PROFILE'}</Text>
          </TouchableOpacity>
        </>
      )}

      {/* Large Logout Button */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.85}>
        <Text style={styles.logoutBtnText}>LOGOUT / SIGN OUT</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#f8fafc',
    flexGrow: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0f172a',
    marginBottom: 16,
  },
  infoCard: {
    backgroundColor: '#e0e7ff',
    padding: 18,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#3730a3',
    marginBottom: 20,
  },
  infoLabel: {
    fontSize: 16,
    color: '#475569',
    fontWeight: '700',
  },
  infoValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e1b4b',
    marginBottom: 6,
  },
  infoValueSub: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3730a3',
  },
  fieldLabel: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginTop: 14,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#ffffff',
    borderWidth: 2,
    borderColor: '#cbd5e1',
    borderRadius: 14,
    padding: 16,
    fontSize: 18,
    color: '#0f172a',
  },
  langRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  langBtn: {
    flex: 1,
    paddingVertical: 14,
    marginHorizontal: 4,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#cbd5e1',
    backgroundColor: '#ffffff',
    alignItems: 'center',
  },
  langBtnActive: {
    backgroundColor: '#3730a3',
    borderColor: '#3730a3',
  },
  langText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#475569',
  },
  langTextActive: {
    color: '#ffffff',
  },
  saveBtn: {
    backgroundColor: '#3730a3',
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 24,
  },
  saveBtnText: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  logoutBtn: {
    backgroundColor: '#cbd5e1',
    borderWidth: 2,
    borderColor: '#94a3b8',
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 28,
    marginBottom: 20,
  },
  logoutBtnText: {
    color: '#0f172a',
    fontSize: 20,
    fontWeight: 'bold',
  },
});
