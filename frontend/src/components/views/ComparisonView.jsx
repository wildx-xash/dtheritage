import { useEffect, useRef, useState } from 'react';

export default function ComparisonView({
  monument,
  activeComparisonMode,
  onSetComparisonMode,
  showLoftrOverlay,
  onToggleLoftr,
  isActive,
  onOpenEvidenceInReview
}) {
  const viewerRef = useRef(null);
  const canvasRef = useRef(null);
  const handleRef = useRef(null);
  const overlayTopRef = useRef(null);
  const isDraggingRef = useRef(false);
  const [sliderPercent, setSliderPercent] = useState(50);
  const [activeSidebarId, setActiveSidebarId] = useState(monument.evidence[0]?.id ?? null);

  useEffect(() => {
    setActiveSidebarId(monument.evidence[0]?.id ?? null);
  }, [monument]);

  // LoFTR correspondence canvas drawing (ported from drawLoFTRMatches)
  useEffect(() => {
    function drawLoFTRMatches() {
      const canvas = canvasRef.current;
      const frame = viewerRef.current;
      if (!canvas || !frame) return;
      const ctx = canvas.getContext('2d');

      const width = frame.clientWidth;
      const height = frame.clientHeight;
      canvas.width = width;
      canvas.height = height;

      ctx.clearRect(0, 0, width, height);

      if (!monument.matches) return;

      if (activeComparisonMode === 'sbs') {
        const halfWidth = width / 2;
        monument.matches.forEach(match => {
          const x1 = (match.x1 / 800) * halfWidth;
          const y1 = (match.y1 / 500) * height;
          const x2 = halfWidth + ((match.x2 / 800) * halfWidth);
          const y2 = (match.y2 / 500) * height;

          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.strokeStyle = 'rgba(166, 95, 67, 0.45)';
          ctx.lineWidth = 1;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(x1, y1, 2.5, 0, 2 * Math.PI);
          ctx.fillStyle = '#B08A57';
          ctx.fill();

          ctx.beginPath();
          ctx.arc(x2, y2, 2.5, 0, 2 * Math.PI);
          ctx.fillStyle = '#A65F43';
          ctx.fill();
        });
      } else {
        monument.matches.forEach(match => {
          const x = (match.x1 / 800) * width;
          const y = (match.y1 / 500) * height;

          ctx.beginPath();
          ctx.arc(x, y, 3, 0, 2 * Math.PI);
          ctx.fillStyle = 'rgba(176, 138, 87, 0.7)';
          ctx.fill();

          ctx.beginPath();
          ctx.arc(x, y, 6, 0, 2 * Math.PI);
          ctx.strokeStyle = 'rgba(166, 95, 67, 0.4)';
          ctx.stroke();
        });
      }
    }

    if (showLoftrOverlay && isActive) {
      const timeoutId = setTimeout(drawLoFTRMatches, 100);
      window.addEventListener('resize', drawLoFTRMatches);
      return () => {
        clearTimeout(timeoutId);
        window.removeEventListener('resize', drawLoFTRMatches);
      };
    }
  }, [showLoftrOverlay, activeComparisonMode, monument, isActive]);

  // Overlay slider drag (mouse + touch), ported from setupOverlaySlider/updateSlider
  useEffect(() => {
    function updateSlider(clientX) {
      const viewer = viewerRef.current;
      if (!viewer) return;
      const viewerRect = viewer.getBoundingClientRect();
      let offset = clientX - viewerRect.left;
      if (offset < 0) offset = 0;
      if (offset > viewerRect.width) offset = viewerRect.width;
      setSliderPercent((offset / viewerRect.width) * 100);
    }

    function onMouseMove(e) {
      if (!isDraggingRef.current) return;
      updateSlider(e.clientX);
    }
    function onMouseUp() {
      isDraggingRef.current = false;
    }
    function onTouchMove(e) {
      if (!isDraggingRef.current) return;
      updateSlider(e.touches[0].clientX);
    }
    function onTouchEnd() {
      isDraggingRef.current = false;
    }

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('touchmove', onTouchMove);
    window.addEventListener('touchend', onTouchEnd);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('touchend', onTouchEnd);
    };
  }, []);

  const firstImg = monument.timeline[0].img;
  const lastImg = monument.timeline[monument.timeline.length - 1].img;

  return (
    <section id="comparison-view" className={`view-container${isActive ? ' active' : ''}`}>
      <div className="comparison-layout">

        <div className="comparison-pane">
          <div className="comparison-toolbar">
            <div className="comparison-view-mode">
              <button
                id="btn-mode-sbs"
                className={`view-mode-btn${activeComparisonMode === 'sbs' ? ' active' : ''}`}
                onClick={() => onSetComparisonMode('sbs')}
              >
                Side-by-Side
              </button>
              <button
                id="btn-mode-overlay"
                className={`view-mode-btn${activeComparisonMode === 'overlay' ? ' active' : ''}`}
                onClick={() => onSetComparisonMode('overlay')}
              >
                Overlay Slider
              </button>
            </div>

            <div className="match-toggle-container">
              <span className="switch-label">LoFTR Correspondence Overlay</span>
              <label className="switch">
                <input
                  type="checkbox"
                  id="toggle-loftr-matches"
                  checked={showLoftrOverlay}
                  onChange={(e) => onToggleLoftr(e.target.checked)}
                />
                <span className="switch-slider"></span>
              </label>
            </div>
          </div>

          <div className="comparison-viewer-frame" id="comparison-viewer" ref={viewerRef}>

            <div className="comparison-sbs" id="panel-sbs" style={{ display: activeComparisonMode === 'sbs' ? 'grid' : 'none' }}>
              <div className="sbs-half">
                <img id="comp-img-left" src={firstImg} alt="Archival" className="sbs-img" />
                <span className="sbs-label" id="lbl-sbs-left">ARCHIVAL (1860)</span>
              </div>
              <div className="sbs-half" style={{ borderRight: 'none' }}>
                <img id="comp-img-right" src={lastImg} alt="Modern" className="sbs-img" />
                <span className="sbs-label" id="lbl-sbs-right">MODERN (2026)</span>
              </div>
            </div>

            <div className="comparison-overlay-container" id="panel-overlay" style={{ display: activeComparisonMode === 'overlay' ? 'block' : 'none' }}>
              <img id="comp-img-overlay-base" src={lastImg} alt="Modern" className="overlay-img-base" />
              <img
                id="comp-img-overlay-top"
                ref={overlayTopRef}
                src={firstImg}
                alt="Archival"
                className="overlay-img-top"
                style={{ clipPath: `inset(0 ${100 - sliderPercent}% 0 0)` }}
              />
              <div
                className="slider-handle"
                id="slider-drag-handle"
                ref={handleRef}
                style={{ left: `${sliderPercent}%` }}
                onMouseDown={(e) => { isDraggingRef.current = true; e.preventDefault(); }}
                onTouchStart={(e) => { isDraggingRef.current = true; e.preventDefault(); }}
              >
                <div className="slider-button">⇄</div>
              </div>
            </div>

            <canvas
              id="loftr-canvas"
              ref={canvasRef}
              className={`correspondences-canvas${showLoftrOverlay ? ' active' : ''}`}
            ></canvas>

          </div>

          <div>
            <p style={{ fontSize: '0.8rem', fontStyle: 'italic' }}>* Note: The overlay slider is registered utilizing the LoFTR-derived homography matrix for the main facade plane. Parallax artifacts are visible on the background dome and the foreground garden elements.</p>
          </div>
        </div>

        <div className="comparison-stats-pane">
          <div className="archive-card">
            <div className="accession-stamp stamp-brass">Registration Status</div>
            <h3 className="archive-card-title">Alignment Details</h3>

            <div className="status-value-box">
              <span className="status-value-title">Inlier Ratio</span>
              <span className="status-value-data" id="comp-inlier-ratio">{monument.metrics.inlierRatio}</span>
            </div>

            <div style={{ marginTop: '16px' }}>
              <div className="comparison-metric-item">
                <span className="comparison-metric-label">Predicted Points</span>
                <span className="comparison-metric-val" id="comp-predicted-pts">{monument.metrics.predictedPoints}</span>
              </div>
              <div className="comparison-metric-item">
                <span className="comparison-metric-label">RANSAC Inliers</span>
                <span className="comparison-metric-val" id="comp-ransac-inliers">{monument.metrics.ransacInliers}</span>
              </div>
              <div className="comparison-metric-item">
                <span className="comparison-metric-label">Reprojection RMSE</span>
                <span className="comparison-metric-val" id="comp-reproj-rmse">{monument.metrics.reprojRmse}</span>
              </div>
              <div className="comparison-metric-item">
                <span className="comparison-metric-label">Facial Alignment</span>
                <span className="comparison-metric-val" style={{ color: 'var(--color-success)' }} id="comp-facade-align">{monument.metrics.facadeAlign}</span>
              </div>
              <div className="comparison-metric-item" style={{ borderBottom: 'none' }}>
                <span className="comparison-metric-label">Depth/Parallax Gap</span>
                <span className="comparison-metric-val" style={{ color: 'var(--color-warning)' }} id="comp-parallax-gap">{monument.metrics.parallaxGap}</span>
              </div>
            </div>
          </div>

          <div className="archive-card">
            <h3 className="archive-card-title">Visible Changes</h3>
            <p style={{ fontSize: '0.8rem', marginBottom: '12px' }}>Candidate change regions detected in the facade area plane:</p>

            <div className="candidate-changes-sidebar-list" id="candidate-changes-sidebar">
              {monument.evidence.length === 0 ? (
                <div className="change-item-sidebar">
                  <div className="change-item-desc">
                    <span className="change-item-name">No verified candidate evidence</span>
                    <span className="change-item-meta">Awaiting the versioned CV output bundle.</span>
                  </div>
                </div>
              ) : (
                monument.evidence.map(ev => (
                  <div
                    key={ev.id}
                    className={`change-item-sidebar${ev.id === activeSidebarId ? ' active' : ''}`}
                    data-id={ev.id}
                    onClick={() => {
                      setActiveSidebarId(ev.id);
                      onOpenEvidenceInReview(ev.id);
                    }}
                  >
                    <div className="change-item-desc">
                      <span className="change-item-name">{ev.title}</span>
                      <span className="change-item-meta">{ev.feature} · Conf: {ev.confidence}</span>
                    </div>
                    <div>
                      <span className={`status-dot ${ev.status === 'Accepted' ? 'success' : (ev.status === 'Rejected' ? 'error' : 'warning')}`}></span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
