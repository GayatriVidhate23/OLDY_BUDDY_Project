import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useStore } from './store';
import Login from './Login';
import CaregiverDashboard from './CaregiverDashboard';
import ElderDashboard from './ElderDashboard';
import Landing from './Landing';
import { Link } from 'react-router-dom';

function PrivateRoute({ children }: { children: any }) {
  const token = useStore((state: any) => state.token);
  return token ? children : <Navigate to="/login" />;
}

function RoleRouter() {
  const role = useStore((state: any) => state.role);
  if (role === 'ELDER') {
    return <ElderDashboard />;
  } else if (role === 'CAREGIVER' || role === 'FAMILY') {
    return <CaregiverDashboard />;
  } else {
    return <div>Loading or unknown role...</div>;
  }
}

export function Navbar() {
  const token = useStore((state: any) => state.token);
  const logout = useStore((state: any) => state.logout);
  return (
    <div className="nav">
      <Link to="/" className="nav-brand">Oldy Buddy</Link>
      <div className="nav-links">
        <Link to="/">Home</Link>
        {token && <Link to="/dashboard">Dashboard</Link>}
      </div>
      <div>
        {token ? (
          <button className="btn btn-dark" onClick={() => logout()}>Logout</button>
        ) : (
          <Link to="/login" className="btn btn-lime">Login</Link>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<PrivateRoute><RoleRouter /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}
