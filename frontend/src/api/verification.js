// Ported from the vanilla app.js verification data loader.
// Behavior preserved: Supabase REST fetch when window.SUPABASE_CONFIG is set
// (with apikey/Authorization headers), otherwise fall back to the local
// static JSON bundle served from public/data/verification/<monument>/.
import { formatMatrix, evidenceForUi } from '../data/monumentsData.js';

const SOURCES = {
  humayun: ['registration_metrics_pair02.json', 'candidate_evidence.json'],
  sanchi: ['registration_metrics_gateway.json', 'candidate_evidence.json'],
  qutb: ['registration_metrics_full_height.json', 'candidate_evidence.json']
};

async function loadVerificationData(monumentId, files) {
  const config = window.SUPABASE_CONFIG || {};
  if (config.url && config.anonKey) {
    const headers = { apikey: config.anonKey, Authorization: `Bearer ${config.anonKey}` };
    const base = config.url.replace(/\/$/, '') + '/rest/v1/';
    const registrationResponse = await fetch(
      `${base}registrations?monument_id=eq.${monumentId}&select=*&order=created_at.desc&limit=1`,
      { headers }
    );
    const candidateResponse = await fetch(
      `${base}evidence_candidates?monument_id=eq.${monumentId}&select=*&order=candidate_id`,
      { headers }
    );
    if (!registrationResponse.ok || !candidateResponse.ok) {
      throw new Error('Supabase data request failed. Check the project URL, anon key, and read policies.');
    }
    const registrations = await registrationResponse.json();
    const candidates = await candidateResponse.json();
    if (!registrations.length) throw new Error(`No Supabase registration found for ${monumentId}.`);
    return { metrics: registrations[0].metrics, evidence: { candidates } };
  }

  const base = `/data/verification/${monumentId}/`;
  const [metrics, evidence] = await Promise.all(files.map(file => fetch(base + file).then(response => {
    if (!response.ok) throw new Error(`Unable to load ${file}`);
    return response.json();
  })));
  return { metrics, evidence };
}

// Returns { monumentsData, heroPhoto } on success, or null on failure
// (mirrors the original's console.warn-and-skip fallback behavior).
export async function loadVerificationBundle(monumentsData) {
  try {
    const updated = {};
    await Promise.all(Object.entries(SOURCES).map(async ([monumentId, files]) => {
      const { metrics, evidence } = await loadVerificationData(monumentId, files);
      const ransac = metrics.ransac || {};
      const geometry = (metrics.geometric_error || {}).over_ransac_inliers || {};
      const homography = metrics.homography || {};
      const valid = metrics.status === 'success';

      const current = monumentsData[monumentId];
      const nextMetrics = {
        ...current.metrics,
        predictedPoints: (metrics.correspondences || {}).total_predicted ?? '—',
        ransacInliers: ransac.inlier_count ?? '—',
        inlierRatio: ransac.inlier_ratio == null ? '—' : `${(ransac.inlier_ratio * 100).toFixed(1)}%`,
        reprojRmse: geometry.rmse_px == null ? '—' : `${geometry.rmse_px.toFixed(2)} px`,
        facadeAlign: valid ? 'Validated (bounded)' : 'Not validated',
        parallaxGap: valid ? 'Bounded by trust regions' : 'Registration rejected',
        hMatrix: homography.matrix_inference_coords ? formatMatrix(homography.matrix_inference_coords) : [["—", "—", "—"], ["—", "—", "—"], ["—", "—", "—"]],
        hCond: homography.condition_number ? homography.condition_number.toExponential(2) : '—',
        hDet: homography.determinant == null ? '—' : homography.determinant.toFixed(3),
        hSupport: valid ? 'Validated' : 'Rejected',
        vSupport: valid ? 'Bounded' : 'Rejected',
        hullCoverage: ransac.inlier_hull_area_fraction_of_archival_inference == null ? '—' : `${(ransac.inlier_hull_area_fraction_of_archival_inference * 100).toFixed(2)}%`,
        confMean: (metrics.correspondences || {}).confidence_distribution?.mean == null ? '—' : `${((metrics.correspondences.confidence_distribution.mean) * 100).toFixed(1)}%`
      };

      updated[monumentId] = {
        ...current,
        metrics: nextMetrics,
        evidence: (evidence.candidates || []).map(evidenceForUi),
        statusText: valid
          ? 'BOUNDED REGISTRATION: CHANGE EVIDENCE VIABLE'
          : 'REGISTRATION REJECTED: NO CHANGE EVIDENCE',
        statusType: valid ? 'success' : 'warning'
      };
    }));

    return {
      monumentsData: { ...monumentsData, ...updated },
      heroPhoto: {
        caption: "Humayun's Tomb, Delhi · 1860 · Wikimedia Commons / British Library",
        stamp: 'HUM-H01'
      }
    };
  } catch (error) {
    console.warn('Verification data could not be loaded. Serve this static folder through a local web server to enable the JSON bundle.', error);
    return null;
  }
}
