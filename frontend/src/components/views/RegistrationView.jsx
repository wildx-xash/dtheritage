function hullCoverageBarWidth(hullCoverage) {
  const value = parseFloat(hullCoverage);
  return Number.isNaN(value) ? '0%' : `${value * 10}%`;
}

export default function RegistrationView({ monument, isActive }) {
  const { metrics } = monument;

  return (
    <section id="registration-view" className={`view-container${isActive ? ' active' : ''}`}>
      <div className="registration-grid">

        <div className="scientific-matrix-box">
          <div className="scientific-matrix-title">Estimated Homography Matrix (H)</div>
          <p style={{ fontSize: '0.75rem', color: 'rgba(244, 235, 221, 0.7)', marginBottom: '16px' }}>3x3 Perspective Projection Matrix computed from RANSAC inliers mapping historical coordinates into modern image space.</p>

          <div className="homography-matrix">
            {metrics.hMatrix.map((row, rowIdx) => (
              <div className="homography-row" id={`h-row-${rowIdx}`} key={rowIdx}>
                {row.map((value, colIdx) => <span key={colIdx}>{value}</span>)}
              </div>
            ))}
          </div>

          <div className="scientific-matrix-footer">
            <div>Condition Number: <span id="h-cond">{metrics.hCond}</span></div>
            <div style={{ marginTop: '4px' }}>Determinant: <span id="h-det">{metrics.hDet}</span></div>
          </div>
        </div>

        <div className="archive-card">
          <div className="accession-stamp stamp-brass">Diagnostic Bounds</div>
          <h3 className="archive-card-title">Geometric Registration Diagnostics</h3>
          <p style={{ marginBottom: '20px' }}>Analysis of RANSAC correspondence distribution, spatial coverage, and structural support ratios across the monument facade.</p>

          <div className="chart-vintage-bar-container">

            <div className="vintage-bar-wrapper">
              <div className="vintage-bar-lbl-row">
                <span>Horizontal Support Spread (Width Coverage)</span>
                <span id="stat-h-support">{metrics.hSupport}</span>
              </div>
              <div className="vintage-bar-outline">
                <div className="vintage-bar-fill success" id="bar-h-support" style={{ width: metrics.hSupport }}></div>
              </div>
            </div>

            <div className="vintage-bar-wrapper">
              <div className="vintage-bar-lbl-row">
                <span>Vertical Support Spread (Height Coverage)</span>
                <span id="stat-v-support">{metrics.vSupport}</span>
              </div>
              <div className="vintage-bar-outline">
                <div className="vintage-bar-fill warning" id="bar-v-support" style={{ width: metrics.vSupport }}></div>
              </div>
            </div>

            <div className="vintage-bar-wrapper">
              <div className="vintage-bar-lbl-row">
                <span>Spatial Hull Coverage of Facade Plane</span>
                <span id="stat-hull-coverage">{metrics.hullCoverage}</span>
              </div>
              <div className="vintage-bar-outline">
                <div className="vintage-bar-fill warning" id="bar-hull-coverage" style={{ width: hullCoverageBarWidth(metrics.hullCoverage) }}></div>
              </div>
            </div>

            <div className="vintage-bar-wrapper">
              <div className="vintage-bar-lbl-row">
                <span>Inlier Correspondence Confidence Mean</span>
                <span id="stat-conf-mean">{metrics.confMean}</span>
              </div>
              <div className="vintage-bar-outline">
                <div className="vintage-bar-fill success" id="bar-conf-mean" style={{ width: metrics.confMean }}></div>
              </div>
            </div>

          </div>
        </div>

        <div className="manual-fallback-box">
          <div className="fallback-content">
            <h4 className="fallback-title">Initiate Manual Alignment Fallback</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--secondary-brown)' }}>If automated LoFTR correspondences fail due to severe architectural modification or view angles, configure manual key landmark correspondences.</p>
          </div>
          <div>
            <button
              className="btn btn-outline"
              style={{ borderColor: 'var(--color-error)', color: 'var(--color-error)' }}
              onClick={() => alert('Manual landmark alignment is a planned human-in-the-loop workflow. This static UI does not fabricate a registration result; use validated landmark output when it is available.')}
            >
              Simulate Landmark Alignment
            </button>
          </div>
        </div>

      </div>
    </section>
  );
}
