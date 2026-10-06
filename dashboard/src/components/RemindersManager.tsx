import React, { useState } from 'react';

interface ActivityItem {
  id: number;
  elder_id: number;
  activity_type: string;
  description: string;
  status: string;
  timestamp: string;
}

interface RemindersManagerProps {
  activities: ActivityItem[];
  onAddReminder: (desc: string) => void;
  onToggleStatus: (id: number, currentStatus: string) => void;
}

export const RemindersManager: React.FC<RemindersManagerProps> = ({ activities, onAddReminder, onToggleStatus }) => {
  const [newDesc, setNewDesc] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDesc.trim()) return;
    onAddReminder(newDesc.trim());
    setNewDesc('');
  };

  return (
    <div className="card">
      <h3 style={{ fontSize: '20px', fontWeight: 800, marginBottom: '16px' }}>⏰ Elder Reminders & Schedule</h3>

      {/* Add New Reminder Form */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
        <input
          type="text"
          placeholder="New Caregiver Reminder (e.g. Give Blood Pressure Medicine at 2 PM)"
          value={newDesc}
          onChange={(e) => setNewDesc(e.target.value)}
          style={{ flex: 1, padding: '14px', borderRadius: '12px', border: '1px solid #cbd5e1', fontSize: '15px' }}
        />
        <button type="submit" className="btn-blue">Add Reminder</button>
      </form>

      {/* List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {activities.map((act) => {
          const isDone = act.status === 'COMPLETED';
          return (
            <div
              key={act.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '16px',
                borderRadius: '12px',
                backgroundColor: isDone ? '#f8fafc' : '#ffffff',
                border: '1px solid #e2e8f0',
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: '16px', textDecoration: isDone ? 'line-through' : 'none', color: isDone ? '#64748b' : '#0f172a' }}>
                  {act.description}
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                  {new Date(act.timestamp).toLocaleString()}
                </div>
              </div>

              <button
                onClick={() => onToggleStatus(act.id, act.status)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '10px',
                  fontWeight: 700,
                  fontSize: '13px',
                  backgroundColor: isDone ? '#dcfce7' : '#fef3c7',
                  color: isDone ? '#166534' : '#92400e',
                }}
              >
                {isDone ? '✓ COMPLETED' : 'MARK DONE'}
              </button>
            </div>
          );
        })}

        {activities.length === 0 && (
          <div style={{ textTransform: 'none', color: '#94a3b8', textAlign: 'center', padding: '24px' }}>
            No reminders scheduled yet for this elder.
          </div>
        )}
      </div>
    </div>
  );
};
