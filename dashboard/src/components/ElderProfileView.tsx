import React, { useState, useEffect } from 'react';
import { dashboardApi } from '../api';

interface ElderProfileViewProps {
  elderId: number;
}

export const ElderProfileView: React.FC<ElderProfileViewProps> = ({ elderId }) => {
  const [emergencyContact, setEmergencyContact] = useState('');
  const [medicalInfo, setMedicalInfo] = useState('');
  const [routines, setRoutines] = useState('');
  const [loading, setLoading] = useState(false);
  const [savedMsg, setSavedMsg] = useState('');

  useEffect(() => {
    setLoading(true);
    dashboardApi.getElderProfile(elderId)
      .then((p) => {
        setEmergencyContact(p.emergency_contact || '');
        setMedicalInfo(JSON.stringify(p.medical_info || {}, null, 2));
        setRoutines(JSON.stringify(p.routines || {}, null, 2));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [elderId]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let parsedMed = {};
      let parsedRoutines = {};
      try { parsedMed = JSON.parse(medicalInfo); } catch (_) { parsedMed = { text: medicalInfo }; }
      try { parsedRoutines = JSON.parse(routines); } catch (_) { parsedRoutines = { text: routines }; }

      await dashboardApi.updateElderProfile(elderId, {
        emergency_contact: emergencyContact,
        medical_info: parsedMed,
        routines: parsedRoutines,
      });

      setSavedMsg('✓ Profile updated successfully!');
      setTimeout(() => setSavedMsg(''), 3000);
    } catch (err: any) {
      alert('Error updating profile: ' + err.message);
    }
  };

  return (
    <div className="card">
      <h3 style={{ fontSize: '20px', fontWeight: 800, marginBottom: '16px' }}>👤 Elder Profile & Personal Context</h3>

      {loading ? (
        <div>Loading profile...</div>
      ) : (
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontWeight: 700, fontSize: '14px', display: 'block', marginBottom: '6px' }}>Emergency Contact Phone:</label>
            <input
              type="text"
              value={emergencyContact}
              onChange={(e) => setEmergencyContact(e.target.value)}
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #cbd5e1' }}
            />
          </div>

          <div>
            <label style={{ fontWeight: 700, fontSize: '14px', display: 'block', marginBottom: '6px' }}>Medical Info & Conditions (JSON / Notes):</label>
            <textarea
              rows={4}
              value={medicalInfo}
              onChange={(e) => setMedicalInfo(e.target.value)}
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #cbd5e1', fontFamily: 'monospace' }}
            />
          </div>

          <div>
            <label style={{ fontWeight: 700, fontSize: '14px', display: 'block', marginBottom: '6px' }}>Daily Routines & Schedules (JSON / Notes):</label>
            <textarea
              rows={4}
              value={routines}
              onChange={(e) => setRoutines(e.target.value)}
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #cbd5e1', fontFamily: 'monospace' }}
            />
          </div>

          <button type="submit" className="btn-blue" style={{ alignSelf: 'flex-start' }}>Save Elder Context</button>
          {savedMsg && <div style={{ color: '#166534', fontWeight: 700 }}>{savedMsg}</div>}
        </form>
      )}
    </div>
  );
};
