export default function ProvenanceView({ monumentsData, isActive }) {
  return (
    <section id="provenance-view" className={`view-container${isActive ? ' active' : ''}`}>
      <div className="dossier-grid">

        <div className="provenance-table-card">
          <div className="accession-stamp">Ledger Registries</div>
          <h3 className="archive-card-title">Conservation Image Provenance Ledger</h3>
          <p style={{ marginBottom: '20px' }}>Auditable documentation for each photographic record, guaranteeing metadata integrity and heritage citation.</p>

          <div className="archival-table-container">
            <table className="archival-table" id="provenance-ledger-table">
              <thead>
                <tr>
                  <th>Accession No</th>
                  <th>Monument</th>
                  <th>Source Collection</th>
                  <th>Epoch</th>
                  <th>Photographer</th>
                  <th>License</th>
                </tr>
              </thead>
              <tbody id="provenance-table-body">
                {Object.keys(monumentsData).map(monId => {
                  const data = monumentsData[monId];
                  return data.timeline.map(record => (
                    <tr key={record.stamp}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--accent-rose)' }}>{record.stamp}</td>
                      <td style={{ fontFamily: 'var(--font-serif)', fontSize: '1rem', fontWeight: 600 }}>{data.name}</td>
                      <td>{record.source}</td>
                      <td>{record.year}</td>
                      <td>{record.author}</td>
                      <td><span className={`badge ${record.license === 'Public Domain' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.65rem' }}>{record.license}</span></td>
                    </tr>
                  ));
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="uncertainty-guide-card">
          <h3 className="archive-card-title">Registration Uncertainty Framework</h3>
          <p>Our system operates under the <strong>Human-in-the-Loop review principle</strong>. Geometric and pixel difference confidence is classified into distinct trust bands:</p>

          <div className="tier-list">
            <div className="tier-item trusted">
              <div className="tier-name-row">
                <span className="tier-name">TRUSTED (High Confidence)</span>
                <span className="badge badge-success" style={{ fontSize: '0.6rem' }}>Inliers &gt; 150</span>
              </div>
              <p className="tier-desc">Valid homography confirmed on the local structure plane. Low reprojection RMSE (&lt; 2px). Suitable for direct difference analysis.</p>
            </div>

            <div className="tier-item marginal">
              <div className="tier-name-row">
                <span className="tier-name">MARGINAL (Medium Confidence)</span>
                <span className="badge badge-warning" style={{ fontSize: '0.6rem' }}>Inliers 80 - 150</span>
              </div>
              <p className="tier-desc">Satisfactory feature matching on flat facade but limited spatial coverage. Minor parallax or viewpoint displacement. Requires manual review validation.</p>
            </div>

            <div className="tier-item untrusted">
              <div className="tier-name-row">
                <span className="tier-name">UNTRUSTED (Low Confidence)</span>
                <span className="badge badge-error" style={{ fontSize: '0.6rem' }}>Inliers &lt; 80</span>
              </div>
              <p className="tier-desc">Highly localized correspondences, degenerate matrices, or extreme lighting differences. Geometric analysis is suspended. Fallback landmarks requested.</p>
            </div>

            <div className="tier-item unsupported">
              <div className="tier-name-row">
                <span className="tier-name">UNSUPPORTED (Algorithm Failure)</span>
                <span className="badge" style={{ fontSize: '0.6rem', background: '#eaeaea', color: '#666' }}>Failed</span>
              </div>
              <p className="tier-desc">SIFT/LoFTR failure. Homography conditions degenerate (e.g. collapsed quad). Immediate manual intervention or viewpoint re-acquisition required.</p>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
