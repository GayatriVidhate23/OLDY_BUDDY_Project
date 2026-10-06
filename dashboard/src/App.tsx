import React, { useState, useEffect } from 'react';
import { dashboardApi, getAuthToken, setAuthToken } from './api';
import { Sidebar } from './components/Sidebar';
import { ElderStatusCard } from './components/ElderStatusCard';
import { RemindersManager } from './components/RemindersManager';
import { VoiceCallHistory } from './components/VoiceCallHistory';
import { AlertsFeed } from './components/AlertsFeed';
import { ElderProfileView } from './components/ElderProfileView';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!getAuthToken());
  const [loginEmail, setLoginEmail] = useState('caregiver@example.com');
  const [loginPassword, setLoginPassword] = useState('password');
  const [currentTab, setCurrentTab] = useState('overview');

  const [elderId, setElderId] = useState<number>(1);
  const [overview, setOverview] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [calls, setCalls] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [calling, setCalling] = useState<boolean>(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await dashboardApi.login(loginEmail, loginPassword);
      setAuthToken(res.access_token);
      setIsAuthenticated(true);
    } catch (err: any) {
      alert('Login Failed: ' + err.message);
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    setIsAuthenticated(false);
  };

  const refreshElderData = async () => {
    if (!isAuthenticated) return;
    try {
      const [ov, act, c, alt] = await Promise.all([
        dashboardApi.getDashboardOverview(elderId).catch(() => null),
        dashboardApi.getActivities(elderId).catch(() => []),
        dashboardApi.getVoiceHistory(elderId).catch(() => []),
        dashboardApi.getAlerts(elderId).catch(() => []),
      ]);
      if (ov) setOverview(ov);
      setActivities(act);
      setCalls(c);
      setAlerts(alt);
    } catch (_) {}
  };

  useEffect(() => {
    refreshElderData();
  }, [isAuthenticated, elderId]);

  const handleTriggerCall = async () => {
    setCalling(true);
    try {
      await dashboardApi.triggerOutboundCall(elderId);
      await refreshElderData();
      alert('Automated check-in call executed successfully!');
    } catch (err: any) {
      alert('Call Failed: ' + err.message);
    } finally {
      setCalling(false);
    }
  };

  const handleAddReminder = async (desc: string) => {
    try {
      await dashboardApi.createActivity(elderId, { activity_type: 'REMINDER', description: desc });
      await refreshElderData();
    } catch (err: any) {
      alert('Failed to add reminder: ' + err.message);
    }
  };

  const handleToggleReminderStatus = async (id: number, currentStatus: string) => {
    const nextStatus = currentStatus === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      await dashboardApi.updateActivityStatus(id, nextStatus);
      await refreshElderData();
    } catch (err: any) {
      alert('Failed to update reminder: ' + err.message);
    }
  };

  const handleResolveAlert = async (id: number) => {
    try {
      await dashboardApi.resolveAlert(id);
      await refreshElderData();
    } catch (err: any) {
      alert('Failed to resolve alert: ' + err.message);
    }
  };

  if (!isAuthenticated) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f172a' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '40px', borderRadius: '24px', width: '100%', maxWidth: '420px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)' }}>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{ fontSize: '48px', marginBottom: '8px' }}>👴</div>
            <h1 style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a' }}>Oldy Buddy</h1>
            <p style={{ color: '#64748b', fontSize: '14px' }}>Family & Caregiver Web Portal</p>
          </div>

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ fontWeight: 700, fontSize: '14px', display: 'block', marginBottom: '6px' }}>Caregiver Email:</label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                style={{ width: '100%', padding: '14px', borderRadius: '12px', border: '1px solid #cbd5e1', fontSize: '15px' }}
              />
            </div>

            <div>
              <label style={{ fontWeight: 700, fontSize: '14px', display: 'block', marginBottom: '6px' }}>Password:</label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                style={{ width: '100%', padding: '14px', borderRadius: '12px', border: '1px solid #cbd5e1', fontSize: '15px' }}
              />
            </div>

            <button type="submit" className="btn-lime" style={{ width: '100%', padding: '16px', fontSize: '16px', marginTop: '10px' }}>
              Sign In to Caregiver Portal
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} onLogout={handleLogout} />

      <main className="main-content">
        <div className="header-bar">
          <div>
            <h1 className="header-title">Family & Caregiver Portal</h1>
            <p className="header-subtitle">Real-time status monitoring, AI voice agent logs & emergency alerts</p>
          </div>

          <div className="elder-selector">
            <span style={{ fontWeight: 700, fontSize: '14px', color: '#64748b' }}>Elder ID:</span>
            <input
              type="number"
              value={elderId}
              onChange={(e) => setElderId(Number(e.target.value) || 1)}
              style={{ width: '60px', padding: '6px', borderRadius: '8px', border: '1px solid #cbd5e1', fontWeight: 700 }}
            />
            <button className="btn-blue" style={{ padding: '8px 12px', fontSize: '13px' }} onClick={refreshElderData}>
              🔄 Refresh Data
            </button>
          </div>
        </div>

        {currentTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <ElderStatusCard data={overview} onTriggerCall={handleTriggerCall} calling={calling} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <AlertsFeed alerts={alerts} onResolveAlert={handleResolveAlert} />
              <RemindersManager activities={activities} onAddReminder={handleAddReminder} onToggleStatus={handleToggleReminderStatus} />
            </div>
          </div>
        )}

        {currentTab === 'reminders' && (
          <RemindersManager activities={activities} onAddReminder={handleAddReminder} onToggleStatus={handleToggleReminderStatus} />
        )}

        {currentTab === 'voice' && (
          <VoiceCallHistory calls={calls} onTriggerCall={handleTriggerCall} calling={calling} />
        )}

        {currentTab === 'alerts' && (
          <AlertsFeed alerts={alerts} onResolveAlert={handleResolveAlert} />
        )}

        {currentTab === 'profile' && (
          <ElderProfileView elderId={elderId} />
        )}
      </main>
    </div>
  );
}
