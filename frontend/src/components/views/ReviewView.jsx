import { useEffect, useState } from 'react';

export default function ReviewView({ monument, activeEvidenceId, onSelectEvidence, onReviewAction, onSaveAnnotation, isActive, reviewGlow }) {
  const [reclassifyOpen, setReclassifyOpen] = useState(false);
  const [annotationInput, setAnnotationInput] = useState('');

  useEffect(() => {
    setReclassifyOpen(false);
    setAnnotationInput('');
  }, [activeEvidenceId]);

  const ev = monument.evidence.find(item => item.id === activeEvidenceId);
  const firstImg = monument.timeline[0].img;
  const lastImg = monument.timeline[monument.timeline.length - 1].img;

  function handleAction(action) {
    if (action === 'reclassify') {
      setReclassifyOpen(true);
      return;
    }
    onReviewAction(action);
  }

  function handleSaveAnnotation() {
    const notes = annotationInput.trim();
    if (!notes) return;
    onSaveAnnotation(notes);
    setReclassifyOpen(false);
    setAnnotationInput('');
  }

  return (
    <section id="review-view" className={`view-container${isActive ? ' active' : ''}`}>
      <div className="evidence-layout">

        <div className="evidence-list-pane" id="evidence-queue-list">
          {monument.evidence.length === 0 ? (
            <div className="evidence-row-card">
              <div className="evidence-row-left">
                <span className="evidence-row-title">No verified candidate evidence</span>
                <span className="evidence-row-meta">Candidate evidence will appear after validated output JSON is supplied.</span>
              </div>
            </div>
          ) : (
            monument.evidence.map(item => {
              const isPending = item.status === 'Pending Review' || item.status.startsWith('Pending');
              const isAccepted = item.status === 'Accepted';
              const isRejected = item.status === 'Rejected';
              let badgeClass = 'badge-warning';
              if (isAccepted) badgeClass = 'badge-success';
              if (isRejected) badgeClass = 'badge-error';

              return (
                <div
                  key={item.id}
                  id={`queue-card-${item.id}`}
                  className={`evidence-row-card${item.id === activeEvidenceId ? ' active' : ''}${!isPending ? ' reviewed' : ''}`}
                  onClick={() => onSelectEvidence(item.id)}
                >
                  <div className="evidence-row-left">
                    <span className="evidence-row-title">{item.title}</span>
                    <span className="evidence-row-meta">{item.feature} · Coordinates: {item.coords}</span>
                  </div>
                  <div className="evidence-row-right">
                    <span className="evidence-row-confidence">{item.confidence} Conf.</span>
                    <span className={`badge ${badgeClass}`} id={`badge-status-${item.id}`}>{item.status}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div
          className={`evidence-detail-pane${reviewGlow === 'success' ? ' glow-success' : ''}${reviewGlow === 'error' ? ' glow-error' : ''}`}
          id="evidence-detail-panel"
        >
          {!ev ? (
            <p>No candidate evidence selected.</p>
          ) : (
            <>
              <div className="accession-stamp" id="detail-ev-id">{ev.id}</div>
              <h3 className="archive-card-title" id="detail-ev-title">{ev.title}</h3>

              <div className="evidence-crop-box">
                <div className="evidence-crop-half">
                  <span className="crop-lbl">Archival (1860)</span>
                  <div className="crop-img-container">
                    <img id="detail-crop-archival" src={firstImg} alt="Archival Detail" className="crop-img-el" />
                    <div
                      className="crop-highlight-box"
                      id="detail-crop-box-archival"
                      style={{ left: `${ev.cropArchivalOffset.x}%`, top: `${ev.cropArchivalOffset.y}%`, width: '20%', height: '25%' }}
                    ></div>
                  </div>
                </div>

                <div className="evidence-crop-half">
                  <span className="crop-lbl">Modern (2026)</span>
                  <div className="crop-img-container">
                    <img id="detail-crop-modern" src={lastImg} alt="Modern Detail" className="crop-img-el" />
                    <div
                      className="crop-highlight-box"
                      id="detail-crop-box-modern"
                      style={{ left: `${ev.cropModernOffset.x}%`, top: `${ev.cropModernOffset.y}%`, width: '20%', height: '25%' }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="evidence-meta-block">
                <div className="evidence-meta-row">
                  <span className="evidence-meta-lbl">Detection Algorithm</span>
                  <span className="evidence-meta-val" id="detail-ev-algorithm">{ev.algorithm}</span>
                </div>
                <div className="evidence-meta-row">
                  <span className="evidence-meta-lbl">Geometric Confidence</span>
                  <span className="evidence-meta-val" id="detail-ev-confidence">{ev.confidence}</span>
                </div>
                <div className="evidence-meta-row">
                  <span className="evidence-meta-lbl">Pixel Bounding Coordinates</span>
                  <span className="evidence-meta-val" id="detail-ev-coords">{ev.coords}</span>
                </div>
                <div className="evidence-meta-row">
                  <span className="evidence-meta-lbl">Structural Feature</span>
                  <span className="evidence-meta-val" id="detail-ev-feature">{ev.feature}</span>
                </div>
                <div className="evidence-meta-row" style={{ borderBottom: 'none' }}>
                  <span className="evidence-meta-lbl">Review Status</span>
                  <span className="evidence-meta-val" id="detail-ev-status">
                    {ev.status === 'Accepted' && <span className="badge badge-success">Accepted</span>}
                    {ev.status === 'Rejected' && <span className="badge badge-error">Rejected</span>}
                    {ev.status !== 'Accepted' && ev.status !== 'Rejected' && <span className="badge badge-warning">{ev.status}</span>}
                  </span>
                </div>

                <div className="vintage-bar-wrapper">
                  <div className="vintage-bar-lbl-row">
                    <span>Confidence Level Score</span>
                    <span id="detail-ev-bar-percent">{ev.confidence}</span>
                  </div>
                  <div className="vintage-bar-outline">
                    <div className="vintage-bar-fill" id="detail-ev-bar-fill" style={{ width: ev.confidence }}></div>
                  </div>
                </div>
              </div>

              <div className="evidence-actions-row">
                <button className="btn btn-success" onClick={() => handleAction('accept')}>Accept Evidence</button>
                <button className="btn btn-error" onClick={() => handleAction('reject')}>Reject (Noise)</button>
                <button className="btn btn-outline" style={{ gridColumn: 'span 2' }} onClick={() => handleAction('reclassify')}>Reclassify/Add Annotation</button>
              </div>

              <div className="reclassify-container" id="reclassify-input-block" style={{ display: reclassifyOpen ? 'block' : 'none' }}>
                <label className="custom-select-label" style={{ display: 'block', marginBottom: '8px' }}>Conservator Annotations / Category:</label>
                <input
                  type="text"
                  id="annotation-input"
                  placeholder="Enter custom notes (e.g. Scaffolding visible in contemporary view)"
                  style={{ width: '100%', padding: '10px', border: '1px solid var(--border-sandstone)', borderRadius: '4px', fontFamily: 'var(--font-sans)', background: 'var(--bg-parchment)', marginBottom: '12px' }}
                  value={annotationInput}
                  onChange={(e) => setAnnotationInput(e.target.value)}
                />
                <button className="btn btn-terracotta btn-sm" onClick={handleSaveAnnotation}>Save Annotation</button>
              </div>
            </>
          )}
        </div>

      </div>
    </section>
  );
}
