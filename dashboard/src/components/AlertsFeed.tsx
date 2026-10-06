import React from 'react';

interface AlertItem {
  id: number;
  elder_id: number;
  severity: string;
  message: string;
  is_resolved: boolean;
  timestamp: string;
}

interface AlertsFeedProps {
  alerts: AlertItem[];
  onResolveAlert: (id: number) => void;
}

export const AlertsFeed: React.FC<AlertsFeedProps> = ({ alerts, onResolveAlert }) => {
  return (
    <div className="card">
      <h3 style={{ fontSize: '20px', fontWeight: 800, color: '#ef4444', marginBottom: '16px' }}>
        🚨 Emergency SOS & Policy Alerts
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {alerts.map((alt) => (
          <div
            key={alt.id}
            style={{
              padding: '18px',
              borderRadius: '14px',
              backgroundColor: alt.is_resolved ? '#f8fafc' : '#fef2f2',
              border: alt.is_resolved ? '1px solid #e2e8f0' : '2px solid #ef4444',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontWeight: 800, fontSize: '16px', color: alt.is_resolved ? '#475569' : '#991b1b' }}>
                [{alt.severity}] {alt.message}
              </div>
              <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                {new Date(alt.timestamp).toLocaleString()}
              </div>
            </div>

            {!alt.is_resolved ? (
              <button
                className="btn-lime"
                style={{ padding: '8px 16px', fontSize: '13px' }}
                onClick={() => onResolveAlert(alt.id)}
              >
                ✓ Resolve Alert
              </button>
            ) : (
              <span style={{ fontSize: '13px', fontWeight: 700, color: '#166534' }}>✓ Resolved</span>
            )}
          </div>
        ))}

        {alerts.length === 0 && (
          <div style={{ color: '#166534', backgroundColor: '#dcfce7', padding: '16px', borderRadius: '12px', textAlign: 'center', fontWeight: 700 }}>
            ✓ All clear! No active emergency alerts for this elder.
          </div>
        )}
      </div>
    </div>
  );
};
