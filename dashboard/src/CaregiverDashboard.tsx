import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './api';

function getVitalsStatus(key: string, valStr: string) {
  const val = parseFloat(valStr);
  if (isNaN(val)) return 'NORMAL';
  if (key.includes('Heart')) {
    if (val < 60) return 'LOW';
    if (val > 100) return 'HIGH';
    return 'NORMAL';
  }
  if (key.includes('SpO2')) {
    if (val >= 95) return 'NORMAL';
    if (val >= 90) return 'ATTENTION';
    return 'ALERT';
  }
  if (key.includes('Temperature')) {
    if (val >= 36.0 && val <= 37.5) return 'NORMAL';
    return 'ATTENTION';
  }
  return 'NORMAL';
}

function getStatusColor(status: string) {
  if (status === 'NORMAL') return '#22c55e';
  if (status === 'LOW' || status === 'ATTENTION') return '#f59e0b';
  return '#ef4444';
}

export default function CaregiverDashboard() {
  const queryClient = useQueryClient();
  const { data: elders, isLoading } = useQuery({
    queryKey: ['elders'],
    queryFn: async () => (await apiClient.get('/caregiver/elders')).data
  });

  if (isLoading) return <div className="container">Loading...</div>;
  const elder = elders?.[0]; // Support single elder for simplicity
  if (!elder) return <div className="container">No connected elders found.</div>;

  return <ElderView elder={elder} queryClient={queryClient} />;
}

function ElderView({ elder, queryClient }: { elder: any, queryClient: any }) {
  const { data: profile } = useQuery({
    queryKey: ['profile', elder.id],
    queryFn: async () => (await apiClient.get(`/elders/${elder.id}/profile`)).data
  });
  
  const { data: activities } = useQuery({
    queryKey: ['activities', elder.id],
    queryFn: async () => (await apiClient.get(`/elders/${elder.id}/activities`)).data
  });

  const resolveMutation = useMutation({
    mutationFn: async (activityId: number) => {
      await apiClient.put(`/elders/${elder.id}/activities/${activityId}?status=RESOLVED`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['activities', elder.id] })
  });

  const alerts = activities?.filter((a: any) => a.status === 'PENDING') || [];
  const timeline = activities?.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()) || [];
  const vitals = profile?.preferences?.demo_vitals || {};

  return (
    <div className="container">
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: '3rem', marginBottom: '8px' }}>{elder.full_name || elder.email}</h2>
        {alerts.length > 0 ? (
           <p style={{ fontSize: '1.5rem', color: '#ef4444', fontWeight: 'bold' }}>Needs Attention</p>
        ) : (
           <p style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>Doing well today.</p>
        )}
      </div>
      
      {alerts.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          {alerts.map((a: any) => {
            const isSOS = a.activity_type === 'SOS';
            return (
              <div key={a.id} className="alert alert-danger" style={{ background: 'white', borderLeft: '4px solid #ef4444', alignItems: 'flex-start', flexDirection: 'column' }}>
                <div style={{ width: '100%' }}>
                  <strong style={{ display: 'block', fontSize: '1.1rem', marginBottom: 4 }}>
                    {isSOS ? 'HIGH PRIORITY ALERT: ' : 'ATTENTION: '} {a.description}
                  </strong>
                  <span style={{ color: 'var(--text-muted)' }}>Status: Open</span>
                </div>
                <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
                  <button className="btn btn-danger" onClick={() => resolveMutation.mutate(a.id)}>Acknowledge</button>
                  <button className="btn btn-outline">Call Elder</button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="grid">
        <div className="card card-dark">
          <h3 style={{ margin: 0, color: 'var(--text-muted)' }}>Current Status</h3>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--lime-accent)' }}>● Active</p>
        </div>

        <div className="card">
          <h3 style={{ margin: 0, color: 'var(--text-muted)' }}>Next Reminder</h3>
          <p style={{ fontSize: '1.25rem', fontWeight: 600 }}>Morning medication — 8:30 AM</p>
        </div>
        
        <div className="card" style={{ gridColumn: '1 / -1', background: '#f3f4f6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ margin: 0 }}>Demo Vitals</h3>
            <span className="badge badge-success">Not Medical Device</span>
          </div>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
            {Object.entries(vitals).map(([key, val]: any) => {
              const status = getVitalsStatus(key, val);
              const color = getStatusColor(status);
              return (
                <div key={key}>
                  <strong>{key}:</strong> {val}
                  <span style={{ display: 'block', color, fontWeight: 'bold', fontSize: '0.8rem', marginTop: 2 }}>
                    → {status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
        
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <h3 style={{ margin: 0, marginBottom: 20 }}>Recent Activity</h3>
          {timeline.map((act: any) => {
             const isMissed = act.status === 'MISSED' || (act.status === 'PENDING' && act.activity_type === 'REMINDER');
             const displayStatus = isMissed ? 'MISSED' : act.status;
             return (
              <div key={act.id} style={{ padding: '16px 0', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <strong style={{ fontSize: '1.1rem', color: isMissed ? '#ef4444' : 'inherit' }}>{act.description}</strong>
                  <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Type: {act.activity_type}</div>
                </div>
                <div style={{ textAlign: 'right', color: 'var(--text-muted)' }}>
                  <div style={{ fontWeight: 'bold', color: isMissed ? '#ef4444' : 'inherit' }}>{displayStatus}</div>
                  {new Date(act.timestamp).toLocaleString()}
                </div>
              </div>
             );
          })}
        </div>
      </div>
    </div>
  );
}
