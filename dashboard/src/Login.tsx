import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from './store';
import { apiClient } from './api';

export default function Login() {
  const [email, setEmail] = useState('anjali@example.com');
  const [password, setPassword] = useState('pass');
  const [error, setError] = useState('');
  const setAuth = useStore((state: any) => state.setAuth);
  const navigate = useNavigate();

  const handleLogin = async (e: any) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      
      const res = await apiClient.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      await setAuth(res.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      console.error(err);
      setError('Invalid credentials or server error.');
    }
  };

  return (
    <div style={{ maxWidth: 460, margin: '60px auto', padding: '40px 32px' }} className="card">
      <h2 style={{ textAlign: 'center', marginBottom: 32, fontSize: '2rem' }}>Welcome Back</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      
      <div style={{ marginBottom: 20, display: 'flex', gap: 10, justifyContent: 'center' }}>
        <button className="btn btn-outline" onClick={() => { setEmail('sunita@oldybuddy.com'); setPassword('elder'); }}>Elder Demo</button>
        <button className="btn btn-outline" onClick={() => { setEmail('anjali@example.com'); setPassword('pass'); }}>Caregiver Demo</button>
      </div>

      <form onSubmit={handleLogin}>
        <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
        <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" required />
        <button className="btn btn-primary" style={{ width: '100%', padding: '16px' }} type="submit">Log In to Dashboard</button>
      </form>
    </div>
  );
}
