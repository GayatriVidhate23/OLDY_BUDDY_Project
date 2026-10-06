import React from 'react';

interface OverviewData {
  elder_id: number;
  elder_name: string;
  elder_email: string;
  emergency_contact?: string;
  last_check_in?: string;
  last_interaction?: string;
  status_badge: string;
  active_alerts_count: number;
  today_reminders_count: number;
  completed_reminders_count: number;
  missed_reminders_count: number;
}

interface ElderStatusCardProps {
  data: OverviewData | null;
  onTriggerCall: () => void;
  calling: boolean;
}

export const ElderStatusCard: React.FC<ElderStatusCardProps> = ({ data, onTriggerCall, calling }) => {
  if (!data) return <div className="card">Loading elder status...</div>;

  const getBadgeStyle = (badge: string) => {
    switch (badge) {
      case 'SOS_ALERT':
        return 'badge-sos';
      case 'CHECKED_IN':
        return 'badge-checkedin';
      default:
        return 'badge-checkedin';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner Card */}
      <div className="card" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: '#ffffff' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '14px', color: '#84cc16', fontWeight: 700, letterSpacing: '1px' }}>ACTIVE ELDER MONITORING</div>
            <h2 style={{ fontSize: '32px', fontWeight: 800, marginTop: '4px' }}>{data.elder_name}</h2>
            <p style={{ color: '#94a3b8', marginTop: '4px' }}>Emergency Contact: {data.emergency_contact || 'Not set'}</p>
          </div>
          <div>
            <span className={getBadgeStyle(data.status_badge)}>
              {data.status_badge === 'SOS_ALERT' ? '🚨 EMERGENCY SOS ALERT' : '✓ CHECKED IN & SAFE'}
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#64748b', fontWeight: 600 }}>Last Check-In</div>
          <div style={{ fontSize: '18px', fontWeight: 800, marginTop: '8px', color: '#0f172a' }}>
            {data.last_check_in ? new Date(data.last_check_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Pending'}
          </div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#64748b', fontWeight: 600 }}>Active Alerts</div>
          <div style={{ fontSize: '28px', fontWeight: 800, marginTop: '4px', color: data.active_alerts_count > 0 ? '#ef4444' : '#16a34a' }}>
            {data.active_alerts_count}
          </div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#64748b', fontWeight: 600 }}>Reminders Done</div>
          <div style={{ fontSize: '28px', fontWeight: 800, marginTop: '4px', color: '#3b82f6' }}>
            {data.completed_reminders_count} / {data.today_reminders_count}
          </div>
        </div>

        <div className="card" style={{ textAlign: 'center', justifyContent: 'center', display: 'flex', flexDirection: 'column' }}>
          <button className="btn-lime" onClick={onTriggerCall} disabled={calling}>
            {calling ? '📞 Dialing...' : '📞 Call Elder (Automated)'}
          </button>
        </div>
      </div>
    </div>
  );
};
