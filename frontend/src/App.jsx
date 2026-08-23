import { useEffect, useRef, useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Header from './components/Header.jsx';
import PortfolioView from './components/views/PortfolioView.jsx';
import TimelineView from './components/views/TimelineView.jsx';
import ComparisonView from './components/views/ComparisonView.jsx';
import RegistrationView from './components/views/RegistrationView.jsx';
import ReviewView from './components/views/ReviewView.jsx';
import ProvenanceView from './components/views/ProvenanceView.jsx';
import { createInitialMonumentsData } from './data/monumentsData.js';
import { loadVerificationBundle } from './api/verification.js';

const DEFAULT_HERO_PHOTO = {
  caption: "Humayun's Tomb, Delhi · Circa 1860 · British Library Plate",
  stamp: 'HT-1860-01'
};

function firstEvidenceId(monumentsData, monumentId) {
  return monumentsData[monumentId].evidence[0]?.id ?? null;
}

export default function App() {
  const [monumentsData, setMonumentsData] = useState(createInitialMonumentsData);
  const [heroPhoto, setHeroPhoto] = useState(DEFAULT_HERO_PHOTO);

  const [activeView, setActiveView] = useState('portfolio');
  const [activeMonument, setActiveMonument] = useState('humayun');
  const [activeTimelineIndex, setActiveTimelineIndex] = useState(0);
  const [activeComparisonMode, setActiveComparisonMode] = useState('sbs');
  const [showLoftrOverlay, setShowLoftrOverlay] = useState(false);
  const [activeEvidenceId, setActiveEvidenceId] = useState(() => firstEvidenceId(monumentsData, 'humayun'));
  const [reviewGlow, setReviewGlow] = useState(null);
  const glowTimeoutRef = useRef(null);

  // Tracks the live activeMonument for the one-time bundle-load effect below,
  // so its resolution doesn't reset the user's selection back to a stale value
  // if they switch monuments while the fetch is still in flight.
  const activeMonumentRef = useRef(activeMonument);
  useEffect(() => {
    activeMonumentRef.current = activeMonument;
  }, [activeMonument]);

  // Initial verification bundle load (Supabase, falling back to local JSON),
  // ported from the DOMContentLoaded -> loadVerificationBundle() call.
  useEffect(() => {
    let cancelled = false;
    loadVerificationBundle(monumentsData).then(result => {
      if (cancelled || !result) return;
      setMonumentsData(result.monumentsData);
      setHeroPhoto(result.heroPhoto);
      setActiveTimelineIndex(0);
      setActiveEvidenceId(firstEvidenceId(result.monumentsData, activeMonumentRef.current));
    });
    return () => { cancelled = true; };
    // Intentionally runs once on mount only, mirroring the original's single
    // DOMContentLoaded -> loadVerificationBundle() call.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => () => clearTimeout(glowTimeoutRef.current), []);

  function selectMonument(id) {
    setActiveMonument(id);
    setActiveTimelineIndex(0);
    setActiveEvidenceId(firstEvidenceId(monumentsData, id));
  }

  function openEvidenceInReview(evId) {
    setActiveEvidenceId(evId);
    setActiveView('review');
  }

  function updateActiveEvidence(updater) {
    setMonumentsData(prev => {
      const monument = prev[activeMonument];
      const nextEvidence = monument.evidence.map(item =>
        item.id === activeEvidenceId ? updater(item) : item
      );
      return {
        ...prev,
        [activeMonument]: { ...monument, evidence: nextEvidence }
      };
    });
  }

  function handleReviewAction(action) {
    if (!activeEvidenceId) return;
    if (action === 'accept') {
      updateActiveEvidence(item => ({ ...item, status: 'Accepted' }));
      setReviewGlow('success');
    } else if (action === 'reject') {
      updateActiveEvidence(item => ({ ...item, status: 'Rejected' }));
      setReviewGlow('error');
    }
    clearTimeout(glowTimeoutRef.current);
    glowTimeoutRef.current = setTimeout(() => setReviewGlow(null), 500);
  }

  function handleSaveAnnotation(notes) {
    if (!activeEvidenceId || !notes) return;
    updateActiveEvidence(item => ({ ...item, status: `Reclassified: ${notes}` }));
  }

  const monument = monumentsData[activeMonument];

  return (
    <div className="app-container">
      <Sidebar activeView={activeView} onNavigate={setActiveView} />

      <main className="main-content">
        <Header
          activeView={activeView}
          activeMonument={activeMonument}
          onMonumentChange={selectMonument}
          monument={monument}
        />

        <PortfolioView
          isActive={activeView === 'portfolio'}
          monumentsData={monumentsData}
          heroPhoto={heroPhoto}
          onNavigate={setActiveView}
          onInspect={selectMonument}
        />

        <TimelineView
          isActive={activeView === 'timeline'}
          monument={monument}
          activeTimelineIndex={activeTimelineIndex}
          onSetTimelineIndex={setActiveTimelineIndex}
        />

        <ComparisonView
          isActive={activeView === 'comparison'}
          monument={monument}
          activeComparisonMode={activeComparisonMode}
          onSetComparisonMode={setActiveComparisonMode}
          showLoftrOverlay={showLoftrOverlay}
          onToggleLoftr={setShowLoftrOverlay}
          onOpenEvidenceInReview={openEvidenceInReview}
        />

        <RegistrationView
          isActive={activeView === 'registration'}
          monument={monument}
        />

        <ReviewView
          isActive={activeView === 'review'}
          monument={monument}
          activeEvidenceId={activeEvidenceId}
          onSelectEvidence={setActiveEvidenceId}
          onReviewAction={handleReviewAction}
          onSaveAnnotation={handleSaveAnnotation}
          reviewGlow={reviewGlow}
        />

        <ProvenanceView
          isActive={activeView === 'provenance'}
          monumentsData={monumentsData}
        />
      </main>
    </div>
  );
}
