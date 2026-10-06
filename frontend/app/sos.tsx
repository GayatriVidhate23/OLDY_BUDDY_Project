import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, Modal, ActivityIndicator } from 'react-native';
import { api } from '../services/api';
import { authStore } from '../store/authStore';

export default function SOSScreen() {
  const user = authStore.getUser();
  const [confirmModalVisible, setConfirmModalVisible] = useState(false);
  const [sending, setSending] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);

  const promptConfirmation = () => {
    setConfirmModalVisible(true);
  };

  const handleSendSOS = async () => {
    setConfirmModalVisible(false);
    if (!user) {
      Alert.alert('Error', 'User session not found. Please log in.');
      return;
    }

    setSending(true);
    try {
      await api.triggerSOS(user.id);
      setStatusText('🚨 EMERGENCY SOS SENT! Caregivers and family contacts have been alerted.');
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to send SOS signal. Please try calling directly.');
      setStatusText('Failed to send SOS alert over network.');
    } finally {
      setSending(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.pageTitle}>Emergency SOS Help</Text>
      <Text style={styles.pageSubtitle}>
        Press the big red button below if you need immediate assistance or care.
      </Text>

      {/* Big Emergency Button */}
      <TouchableOpacity
        style={styles.sosCircleBtn}
        activeOpacity={0.8}
        onPress={promptConfirmation}
        disabled={sending}
      >
        {sending ? (
          <ActivityIndicator size="large" color="#ffffff" />
        ) : (
          <>
            <Text style={styles.sosCircleIcon}>🆘</Text>
            <Text style={styles.sosCircleText}>I NEED HELP</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Status Output */}
      {statusText ? (
        <View style={styles.statusBox}>
          <Text style={styles.statusContent}>{statusText}</Text>
        </View>
      ) : null}

      {/* Confirmation Modal for Elderly Safety */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={confirmModalVisible}
        onRequestClose={() => setConfirmModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Confirm Emergency SOS</Text>
            <Text style={styles.modalMessage}>
              Are you sure you want to send an emergency alert to your caregivers and contacts?
            </Text>

            <TouchableOpacity
              style={styles.modalConfirmBtn}
              onPress={handleSendSOS}
              activeOpacity={0.85}
            >
              <Text style={styles.modalConfirmText}>YES, SEND HELP NOW</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.modalCancelBtn}
              onPress={() => setConfirmModalVisible(false)}
              activeOpacity={0.85}
            >
              <Text style={styles.modalCancelText}>CANCEL</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  pageTitle: {
    fontSize: 30,
    fontWeight: 'bold',
    color: '#991b1b',
    textAlign: 'center',
  },
  pageSubtitle: {
    fontSize: 18,
    color: '#475569',
    textAlign: 'center',
    marginVertical: 14,
    paddingHorizontal: 10,
  },
  sosCircleBtn: {
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: '#dc2626',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 24,
    borderWidth: 6,
    borderColor: '#991b1b',
    elevation: 8,
    shadowColor: '#dc2626',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
  },
  sosCircleIcon: {
    fontSize: 48,
    marginBottom: 6,
  },
  sosCircleText: {
    fontSize: 26,
    fontWeight: '900',
    color: '#ffffff',
    letterSpacing: 1,
  },
  statusBox: {
    backgroundColor: '#fef2f2',
    borderWidth: 2,
    borderColor: '#dc2626',
    padding: 18,
    borderRadius: 14,
    marginTop: 10,
    marginHorizontal: 16,
  },
  statusContent: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#991b1b',
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    padding: 24,
    width: '100%',
    maxWidth: 360,
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#dc2626',
  },
  modalTitle: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#991b1b',
    marginBottom: 10,
  },
  modalMessage: {
    fontSize: 18,
    color: '#334155',
    textAlign: 'center',
    marginBottom: 20,
  },
  modalConfirmBtn: {
    backgroundColor: '#dc2626',
    paddingVertical: 18,
    width: '100%',
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  modalConfirmText: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  modalCancelBtn: {
    backgroundColor: '#cbd5e1',
    paddingVertical: 16,
    width: '100%',
    borderRadius: 14,
    alignItems: 'center',
  },
  modalCancelText: {
    color: '#1e293b',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
