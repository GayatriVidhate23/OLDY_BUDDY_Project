import React from 'react';

interface VoiceCallItem {
  id: number;
  elder_id: number;
  phone_number: string;
  call_type: string;
  status: string;
  duration_seconds: number;
  transcript: string;
  ai_summary: string;
  timestamp: string;
}

interface VoiceCallHistoryProps {
  calls: VoiceCallItem[];
  onTriggerCall: () => void;
  calling: boolean;
}

export const VoiceCallHistory: React.FC<VoiceCallHistoryProps> = ({ calls, onTriggerCall, calling }) => {
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h3 style={{ fontSize: '20px', fontWeight: 800 }}>📞 Voice Agent Call History</h3>
          <p style={{ fontSize: '14px', color: '#64748b' }}>Automated check-in calls, transcripts, and AI summaries</p>
        </div>
        <button className="btn-lime" onClick={onTriggerCall} disabled={calling}>
          {calling ? 'Dialing Call...' : '📞 Trigger Automated Call'}
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {calls.map((c) => (
          <div
            key={c.id}
            style={{
              padding: '20px',
              borderRadius: '16px',
              border: '1px solid #e2e8f0',
              backgroundColor: '#f8fafc',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontWeight: 800, fontSize: '15px', color: '#3b82f6' }}>
                [{c.call_type}] • {c.phone_number}
              </span>
              <span style={{ fontSize: '13px', color: '#64748b' }}>
                {new Date(c.timestamp).toLocaleString()} ({c.duration_seconds}s)
              </span>
            </div>

            <div style={{ fontSize: '14px', color: '#0f172a', fontWeight: 600, marginBottom: '8px' }}>
              🤖 AI Summary: <span style={{ fontWeight: 400, color: '#334155' }}>{c.ai_summary || 'N/A'}</span>
            </div>

            {c.transcript && (
              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '12px 16px',
                  borderRadius: '10px',
                  border: '1px solid #cbd5e1',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  color: '#475569',
                }}
              >
                {c.transcript}
              </div>
            )}
          </div>
        ))}

        {calls.length === 0 && (
          <div style={{ color: '#94a3b8', textAlign: 'center', padding: '24px' }}>
            No voice call logs registered yet for this elder.
          </div>
        )}
      </div>
    </div>
  );
};
