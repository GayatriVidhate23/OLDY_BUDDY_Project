import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div>
      <div className="hero">
        <h1>Building the future of care.</h1>
        <p>Oldy Buddy connects elders with families through AI, intelligent automation, and simple interfaces.</p>
        <Link to="/login" className="btn btn-lime" style={{ marginRight: 16 }}>Get Started ↗</Link>
        <button className="btn btn-dark">View Demo</button>
      </div>

      <div className="container">
        <h2 style={{ textAlign: 'center', marginBottom: 48, fontSize: '2.5rem' }}>A global partner in smarter care</h2>
        
        <div className="grid">
          <div className="card card-dark">
            <h3 style={{ fontSize: '3rem', margin: '0 0 16px 0', color: 'var(--lime-accent)' }}>120+</h3>
            <p style={{ margin: 0, opacity: 0.8 }}>Collaborating with leading health providers.</p>
          </div>
          <div className="card">
            <h3 style={{ fontSize: '3rem', margin: '0 0 16px 0' }}>100%</h3>
            <p style={{ margin: 0, color: 'var(--text-muted)' }}>Commitment to seamless integration and reliable SOS alerts.</p>
          </div>
          <div className="card card-lime">
            <h3 style={{ fontSize: '3rem', margin: '0 0 16px 0' }}>24/7</h3>
            <p style={{ margin: 0 }}>Always-on Voice Agent and automated reminders.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
