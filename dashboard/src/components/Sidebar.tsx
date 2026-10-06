import React from 'react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab, onLogout }) => {
  const menuItems = [
    { id: 'overview', label: '📊 Elder Overview', icon: '📊' },
    { id: 'reminders', label: '⏰ Care Reminders', icon: '⏰' },
    { id: 'voice', label: '📞 Voice Agent & Calls', icon: '📞' },
    { id: 'alerts', label: '🚨 Help & Emergency Alerts', icon: '🚨' },
    { id: 'profile', label: '👤 Profile & Settings', icon: '👤' },
  ];

  return (
    <aside className="sidebar">
      <div className="brand-header">
        <div className="brand-icon">👴</div>
        <div>
          <div className="brand-title">Oldy Buddy</div>
          <span className="brand-badge">CAREGIVER PORTAL</span>
        </div>
      </div>

      <nav className="nav-menu">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${currentTab === item.id ? 'active' : ''}`}
            onClick={() => setCurrentTab(item.id)}
          >
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid #334155' }}>
        <button
          className="nav-item"
          onClick={onLogout}
          style={{ color: '#ef4444', backgroundColor: 'transparent' }}
        >
          🚪 Logout Session
        </button>
      </div>
    </aside>
  );
};
