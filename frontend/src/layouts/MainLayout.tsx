import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';

export const MainLayout: React.FC = () => {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{ width: '250px', background: 'var(--bg-secondary)', borderRight: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)' }}>
          <h1 style={{ fontSize: '1.25rem', color: 'var(--accent-blue)', margin: 0 }}>GridLock</h1>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Command Center</div>
        </div>
        
        <nav style={{ padding: '1.5rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <NavLink 
            to="/" 
            style={({ isActive }) => ({
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: isActive ? 'var(--accent-blue-glow)' : 'transparent',
              color: isActive ? '#fff' : 'var(--text-secondary)',
              fontWeight: isActive ? 600 : 500,
              transition: 'all var(--transition-fast)'
            })}
          >
            Browse Historical Events
          </NavLink>
          <NavLink 
            to="/live" 
            style={({ isActive }) => ({
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: isActive ? 'var(--accent-blue-glow)' : 'transparent',
              color: isActive ? '#fff' : 'var(--text-secondary)',
              fontWeight: isActive ? 600 : 500,
              transition: 'all var(--transition-fast)'
            })}
          >
            New Event Advisory
          </NavLink>
          <NavLink 
            to="/outcomes" 
            style={({ isActive }) => ({
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: isActive ? 'var(--accent-blue-glow)' : 'transparent',
              color: isActive ? '#fff' : 'var(--text-secondary)',
              fontWeight: isActive ? 600 : 500,
              transition: 'all var(--transition-fast)'
            })}
          >
            Outcomes Log
          </NavLink>
          <NavLink 
            to="/about" 
            style={({ isActive }) => ({
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: isActive ? 'var(--accent-blue-glow)' : 'transparent',
              color: isActive ? '#fff' : 'var(--text-secondary)',
              fontWeight: isActive ? 600 : 500,
              transition: 'all var(--transition-fast)'
            })}
          >
            About this system
          </NavLink>
        </nav>
      </aside>

      <main style={{ flex: 1, padding: '2rem', height: '100vh', overflowY: 'auto' }}>
        <Outlet />
      </main>
    </div>
  );
};
