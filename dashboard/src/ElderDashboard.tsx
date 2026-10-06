import { useQuery, useMutation } from '@tanstack/react-query';
import { useStore } from './store';
import { apiClient } from './api';

export default function ElderDashboard() {
  const userId = useStore((state: any) => state.userId);
  
  const { data: profile } = useQuery({
    queryKey: ['profile', userId],
    queryFn: async () => (await apiClient.get(`/elders/${userId}/profile`)).data,
    enabled: !!userId
  });

  const sosMutation = useMutation({
    mutationFn: async () => (await apiClient.post(`/elders/${userId}/activities`, { activity_type: 'SOS', description: 'Help requested from dashboard' })).data,
    onSuccess: () => alert("Help is on the way! Caregivers notified."),
    onError: () => alert("Error: Could not send SOS!")
  });
  
  const chatMutation = useMutation({
    mutationFn: async () => (await apiClient.post(`/elders/${userId}/chat`, { message: "Hello Buddy" })).data,
    onSuccess: (data: any) => alert(`Buddy says: ${data.reply}`)
  });

  const vitals = profile?.preferences?.demo_vitals || {};

  return (
    <div className="container" style={{ maxWidth: 800 }}>
      <h1 style={{ fontSize: '4rem', fontWeight: 800, marginBottom: 40 }}>Good Morning, {profile?.user?.full_name?.split(' ')[0] || 'Friend'}</h1>
      
      <div className="card card-lime" style={{ padding: '40px' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: 20 }}>Today's Reminders</h2>
        <ul style={{ fontSize: '1.8rem', lineHeight: '2.5', margin: 0, paddingLeft: 30 }}>
          <li>Medicine</li>
          <li>Lunch</li>
          <li>Doctor appointment</li>
        </ul>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 40 }}>
        <button className="btn btn-primary" style={{ padding: '30px', fontSize: '1.5rem', borderRadius: 24 }} onClick={() => chatMutation.mutate()}>
          🎤 Talk to Oldy Buddy
        </button>
        <button className="btn btn-danger" style={{ padding: '30px', fontSize: '1.5rem', borderRadius: 24 }} onClick={() => sosMutation.mutate()}>
          🆘 I Need Help
        </button>
      </div>

      <div className="card" style={{ background: '#f3f4f6' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: '1.8rem' }}>Daily Activity (Demo)</h3>
          <span className="badge badge-success">Not Medical Device</span>
        </div>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', fontSize: '1.2rem' }}>
          {Object.entries(vitals).map(([key, val]: any) => (
            <div key={key}><strong>{key}:</strong> {val}</div>
          ))}
        </div>
      </div>
    </div>
  );
}
