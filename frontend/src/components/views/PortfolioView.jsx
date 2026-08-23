const CATALOG_CODES = { humayun: '#HT-DEL-01', sanchi: '#SS-MP-02', qutb: '#QM-DEL-03' };

export default function PortfolioView({ monumentsData, heroPhoto, onNavigate, onInspect, isActive }) {
  let totalPending = 0;
  let totalReviewed = 0;
  Object.keys(monumentsData).forEach(key => {
    monumentsData[key].evidence.forEach(ev => {
      if (ev.status.startsWith('Pending')) {
        totalPending++;
      } else {
        totalReviewed++;
      }
    });
  });

  return (
    <section id="portfolio-view" className={`view-container${isActive ? ' active' : ''}`}>
      <div className="grid-2">

        <div className="dashboard-hero">
          <div className="dashboard-hero-content">
            <div>
              <span className="hero-header-label">Digital Conservation Archive</span>
              <h2 className="hero-title">Heritage Conservation Portfolio</h2>
              <p>Curating historical and contemporary photographs as auditable input for bounded, human-reviewed conservation comparison.</p>
            </div>

            <div className="hero-stats-row">
              <div className="hero-stat-box">
                <span className="hero-stat-val">03</span>
                <span className="hero-stat-lbl">Active Monuments</span>
              </div>
              <div className="hero-stat-box">
                <span className="hero-stat-val">18 <span>images</span></span>
                <span className="hero-stat-lbl">Curated Source Images</span>
              </div>
              <div className="hero-stat-box">
                <span className="hero-stat-val">{String(totalReviewed).padStart(2, '0')}</span>
                <span className="hero-stat-lbl">Verified Reviews</span>
              </div>
              <div className="hero-stat-box">
                <span className="hero-stat-val">{String(totalPending).padStart(2, '0')} <span>available</span></span>
                <span className="hero-stat-lbl">Verified Evidence Queue</span>
              </div>
            </div>

            <div>
              <button className="btn btn-terracotta" onClick={() => onNavigate('timeline')}>Open Archive Timelines →</button>
            </div>
          </div>

          <div className="hero-photo-anchor" onClick={() => onNavigate('comparison')}>
            <div className="hero-photo-wrapper">
              <img src="/assets/humayun_archival.jpg" alt="Humayun's Tomb Archival" className="hero-photo-img" />
              <div className="accession-stamp">{heroPhoto.stamp}</div>
            </div>
            <span className="hero-photo-caption">{heroPhoto.caption}</span>
          </div>
        </div>

        <div className="archive-card" style={{ gridColumn: 'span 2' }}>
          <div className="accession-stamp stamp-brass">Portfolio Index</div>
          <h3 className="archive-card-title">Registered Indian Monument Portfolio</h3>

          <div className="archival-table-container">
            <table className="archival-table">
              <thead>
                <tr>
                  <th>Catalog Code</th>
                  <th>Monument Name</th>
                  <th>Location</th>
                  <th>Date Stack</th>
                  <th>LoFTR Inliers</th>
                  <th>Validation Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(monumentsData).map(([id, data]) => {
                  const isValid = data.metrics.facadeAlign !== 'Not validated';
                  const result = isValid
                    ? `${data.metrics.ransacInliers} Inliers (${data.metrics.inlierRatio} ratio)`
                    : `${data.metrics.ransacInliers} Inliers — rejected`;
                  const label = isValid ? 'Bounded registration viable' : 'Registration not validated';
                  return (
                    <tr key={id} style={{ cursor: 'pointer' }} onClick={() => onInspect(id)}>
                      <td>{CATALOG_CODES[id]}</td>
                      <td className="monument-name">{data.name}</td>
                      <td>{data.location}</td>
                      <td>{data.epochs}</td>
                      <td>{result}</td>
                      <td><span className={`badge badge-${data.statusType === 'success' ? 'success' : 'warning'}`}>{label}</span></td>
                      <td>
                        <button
                          className="btn btn-sm btn-outline"
                          onClick={(e) => { e.stopPropagation(); onInspect(id); }}
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="archive-card" style={{ gridColumn: 'span 2' }}>
          <div className="accession-stamp">Feasibility Summary</div>
          <h3 className="archive-card-title">Registration Feasibility & Algorithmic Narrative</h3>
          <p style={{ marginBottom: '16px' }}>Classical descriptor matchers (Vanilla SIFT, SIFT with CLAHE / RootSIFT) failed entirely across the 160-year temporal domain gap due to major lighting, vegetative, and focal variations. The deep learning-based detector-free matcher (LoFTR Outdoor) successfully recovered dense correspondences, validating our geometric pipeline.</p>

          <div className="grid-3">
            <div style={{ borderRight: '1px solid var(--border-sandstone)', paddingRight: '16px' }}>
              <h4 style={{ fontFamily: 'var(--font-sans)', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-error)', marginBottom: '8px' }}>1. Vanilla SIFT</h4>
              <p style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>9 RANSAC inliers. collapsed homography, completely broken alignment. descriptor match failed across eras.</p>
            </div>
            <div style={{ borderRight: '1px solid var(--border-sandstone)', padding: '0 16px' }}>
              <h4 style={{ fontFamily: 'var(--font-sans)', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-warning)', marginBottom: '8px' }}>2. Improved Classical SIFT</h4>
              <p style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>CLAHE normalization + RootSIFT + mutual matching. 4 RANSAC inliers, degenerate matrix. Classical tuning unjustified.</p>
            </div>
            <div style={{ paddingLeft: '16px' }}>
              <h4 style={{ fontFamily: 'var(--font-sans)', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-success)', marginBottom: '8px' }}>3. LoFTR (Outdoor weights)</h4>
              <p style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>182 RANSAC inliers, 0.528 ratio. Valid homography on the main facade. Viewpoint limitations on dome/ground.</p>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
