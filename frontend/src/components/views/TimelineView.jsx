export default function TimelineView({ monument, activeTimelineIndex, onSetTimelineIndex, isActive }) {
  const record = monument.timeline[activeTimelineIndex];
  const progressPercent = (activeTimelineIndex / (monument.timeline.length - 1)) * 100;

  return (
    <section id="timeline-view" className={`view-container${isActive ? ' active' : ''}`}>

      <div className="timeline-slider-container">
        <div className="timeline-ticks-row">
          <h3 className="archive-card-title" id="timeline-monument-name">{monument.name} — Archival Timeline</h3>
          <p>Select a historical epoch to inspect the photo record, origin details, and conservation documentation.</p>

          <div className="timeline-axis">
            <div className="timeline-axis-progress" id="timeline-progress" style={{ width: `${progressPercent}%` }}></div>
            <ul className="timeline-ticks">
              {monument.timeline.map((entry, idx) => (
                <li
                  key={entry.stamp}
                  className={`timeline-tick-node${idx === activeTimelineIndex ? ' active' : ''}`}
                  data-index={idx}
                  onClick={() => onSetTimelineIndex(idx)}
                >
                  <span className="timeline-tick-desc">{entry.era}</span>
                  <span className="timeline-tick-label">{entry.year}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="timeline-detail-box">

        <div className="timeline-detail-image-card">
          <div className="accession-stamp" id="timeline-record-stamp">{record.stamp}</div>
          <div className="timeline-detail-image-wrapper">
            <img id="timeline-photo-el" src={record.img} alt="Archival View" className="timeline-detail-img" />
          </div>
        </div>

        <div className="timeline-detail-info">
          <div>
            <div className="archive-stamp-title">Archival Record Plate</div>
            <h2 id="timeline-record-title" className="heading-serif" style={{ fontSize: '2.2rem', marginBottom: '8px' }}>{record.title}</h2>
            <div className="archival-divider"><span className="divider-motif">◇</span></div>
            <p id="timeline-record-desc" className="timeline-detail-text">{record.desc}</p>
          </div>

          <div className="timeline-meta-grid">
            <div className="timeline-meta-item">
              <span className="timeline-meta-lbl">Photographer / Author</span>
              <span className="timeline-meta-val" id="timeline-meta-author">{record.author}</span>
            </div>
            <div className="timeline-meta-item">
              <span className="timeline-meta-lbl">Date of Capture</span>
              <span className="timeline-meta-val" id="timeline-meta-date">{record.year === '2026' ? 'Year 2026' : `Circa ${record.year}`}</span>
            </div>
            <div className="timeline-meta-item">
              <span className="timeline-meta-lbl">Archive Source</span>
              <span className="timeline-meta-val" id="timeline-meta-source">{record.source}</span>
            </div>
            <div className="timeline-meta-item">
              <span className="timeline-meta-lbl">License Status</span>
              <span className="timeline-meta-val" id="timeline-meta-license">{record.license}</span>
            </div>
            <div className="timeline-meta-item" style={{ gridColumn: 'span 2' }}>
              <span className="timeline-meta-lbl">Conservator Viewpoint Notes</span>
              <span className="timeline-meta-val" id="timeline-meta-notes">{record.notes}</span>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
