const NAV_GROUPS = [
  {
    title: 'Overview',
    items: [
      { target: 'portfolio', icon: '◉', label: 'Portfolio Dashboard' },
      { target: 'timeline', icon: '◇', label: 'Monuments & Timeline' }
    ]
  },
  {
    title: 'Analysis Stack',
    items: [
      { target: 'comparison', icon: '◇', label: 'Image Comparison' },
      { target: 'registration', icon: '◇', label: 'LoFTR Registration' },
      { target: 'review', icon: '◇', label: 'Evidence Review Queue' }
    ]
  },
  {
    title: 'Provenance',
    items: [
      { target: 'provenance', icon: '◇', label: 'Archive Ledger' }
    ]
  }
];

export default function Sidebar({ activeView, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">◈ DTHeritage</div>
        <div className="sidebar-subtitle">Conservation Intel.</div>
      </div>

      <nav className="sidebar-nav">
        {NAV_GROUPS.map(group => (
          <div key={group.title}>
            <div className="nav-group-title">{group.title}</div>
            <ul className="nav-list">
              {group.items.map(item => (
                <li key={item.target}>
                  <a
                    href="#"
                    className={`nav-item${activeView === item.target ? ' active' : ''}`}
                    data-target={item.target}
                    onClick={(e) => {
                      e.preventDefault();
                      onNavigate(item.target);
                    }}
                  >
                    <span className="nav-item-icon">{item.icon}</span> {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-title">SIH 2026 PROTOTYPE</div>
        <div className="sidebar-footer-desc">Heritage & Culture · Team 6</div>
      </div>
    </aside>
  );
}
