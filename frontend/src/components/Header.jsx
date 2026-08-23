const HEADER_TEXT = {
  portfolio: {
    title: 'Conservation Intelligence',
    subtitle: "A digital archive of India's changing heritage structures."
  },
  timeline: {
    title: 'Monument Archives & Timeline',
    subtitle: 'Explore chronological architectural visual plates and restorations.'
  },
  comparison: {
    title: 'Archival & Modern Comparison',
    subtitle: 'Interactive spatial alignment, registration, and delta analysis.'
  },
  registration: {
    title: 'LoFTR Geometric Diagnostics',
    subtitle: 'Scientific verification metrics, homography estimation, and coordinate mappings.'
  },
  review: {
    title: 'Candidate Change Review Queue',
    subtitle: 'Manually verify difference anomalies with expert human-in-the-loop oversight.'
  },
  provenance: {
    title: 'Provenance Registry & Uncertainty Ledger',
    subtitle: 'Auditable photographic citations and error distribution parameters.'
  }
};

export default function Header({ activeView, activeMonument, onMonumentChange, monument }) {
  const { title, subtitle } = HEADER_TEXT[activeView];
  const showMonumentSelector = activeView !== 'portfolio' && activeView !== 'provenance';

  return (
    <header className="content-header">
      <div className="header-title-container">
        <h1 id="page-title" className="header-title">{title}</h1>
        <span id="page-subtitle" className="header-subtitle">{subtitle}</span>
      </div>
      <div className="header-actions">
        <div
          className="custom-select-container"
          id="global-monument-selector-container"
          style={{ display: showMonumentSelector ? 'flex' : 'none' }}
        >
          <label className="custom-select-label" htmlFor="monument-select">Select Monument:</label>
          <select
            id="monument-select"
            className="archival-select"
            value={activeMonument}
            onChange={(e) => onMonumentChange(e.target.value)}
          >
            <option value="humayun">Humayun's Tomb (Testbed)</option>
            <option value="sanchi">Sanchi Stupa (Gateways)</option>
            <option value="qutb">Qutb Minar Complex</option>
          </select>
        </div>
        <div className="hero-status-pill">
          <span className={`status-dot ${monument.statusType}`}></span>
          <span>{monument.statusText.toUpperCase()}</span>
        </div>
      </div>
    </header>
  );
}
