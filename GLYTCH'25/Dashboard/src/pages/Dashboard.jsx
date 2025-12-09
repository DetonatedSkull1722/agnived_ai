function Dashboard({ user, onLogout }) {
  return (
    <div style={{ padding: '20px', color: '#fff', background: '#0f2d25', minHeight: '100vh' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h1>🌿 AgniVed Dashboard</h1>
          <p>Welcome, <strong>{user?.userid}</strong> ({user?.role})</p>
        </div>
        <button
          onClick={onLogout}
          style={{
            padding: '10px 20px',
            background: '#ef4444',
            border: 'none',
            borderRadius: '8px',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          Logout
        </button>
      </header>
      <div>
        <h2>Coming soon: Upload images, view analysis, etc.</h2>
      </div>
    </div>
  );
}

export default Dashboard;