// DTHeritage Sandstone Archive Controller - app.js

// Legacy design dataset. It is overridden below by verified curated project records.
const monumentsData = {
  humayun: {
    name: "Humayun's Tomb",
    location: "Delhi",
    epochs: "1860 – 2026",
    statusText: "LoFTR FEASIBILITY: SUCCESSFUL (FACADE)",
    statusType: "success",
    metrics: {
      predictedPoints: 658,
      ransacInliers: 182,
      inlierRatio: "52.8%",
      reprojRmse: "~1.67 px",
      facadeAlign: "Valid",
      parallaxGap: "Atypical",
      hMatrix: [
        ["0.84221", "-0.01254", "241.521"],
        ["0.01524", "0.83548", "108.204"],
        ["0.00012", "0.00021", "1.00000"]
      ],
      hCond: "~1.90e4",
      hDet: "0.704",
      hSupport: "82%",
      vSupport: "18%",
      hullCoverage: "5.18%",
      confMean: "84.2%"
    },
    timeline: [
      {
        year: "1860",
        era: "Archival Base",
        stamp: "HT-1860-01",
        title: "Southern Facade Plate",
        desc: "Archival record plate from the British Library collection. Photographed by John Burke. Captures the main southern facade, highlighting the double dome and flanking arched bays. This serves as the primary geometric baseline for change intelligence.",
        author: "John Burke",
        source: "British Library Collection",
        license: "Public Domain",
        notes: "Uncalibrated camera, unknown focal length. Flat view of the main sandstone facade. Parasitic vegetation noted near dome base.",
        img: "assets/humayun_archival.jpg"
      },
      {
        year: "1900",
        era: "Survey Era",
        stamp: "HT-1900-02",
        title: "Archaeological Survey",
        desc: "Historic plate captured during the Lord Curzon archaeological restoration surveys. Significant clearance of vegetation around the plinth and initial masonry consolidation work documented on the upper arches.",
        author: "Archaeological Survey of India (ASI)",
        source: "ASI Heritage Archives",
        license: "CC BY 4.0 (Heritage)",
        notes: "Gelatin silver print. Minor perspective skew due to off-axis camera setup.",
        img: "assets/humayun_archival.jpg"
      },
      {
        year: "1947",
        era: "Mid-Century",
        stamp: "HT-1947-04",
        title: "Independence Records",
        desc: "Documentary photograph detailing the state of the surrounding garden walls and water channels. Minor sandstone peeling visible on the eastern corner chhatri structure.",
        author: "Press Information Bureau",
        source: "National Archives of India",
        license: "Government Open Data",
        notes: "Pan-chromatic plate. High atmospheric haze, low contrast.",
        img: "assets/humayun_archival.jpg"
      },
      {
        year: "1993",
        era: "UNESCO Inscription",
        stamp: "HT-1993-01",
        title: "World Heritage Survey",
        desc: "Comprehensive photo-documentation for the UNESCO World Heritage listing dossier. Shows restoration of the central iwan details and re-laying of sandstone paving slabs in the foreground garden area.",
        author: "UNESCO Preservation Team",
        source: "UNESCO World Archives",
        license: "Educational Use Only",
        notes: "Color film scan. Highly comparable view angle to 1860 base.",
        img: "assets/humayun_modern.jpg"
      },
      {
        year: "2026",
        era: "Contemporary",
        stamp: "HT-2026-09",
        title: "Contemporary Crowd View",
        desc: "Modern crowd-sourced high-resolution digital photograph aligned to the historical baseline viewpoint. Fully calibrated to document active sandstone erosion and structural shifts.",
        author: "DTHeritage Team Scan",
        source: "Contemporary Stack",
        license: "Project Custody",
        notes: "Fully digital CMOS sensor. Viewpoint parallax compensated using dense LoFTR registration mapping.",
        img: "assets/humayun_modern.jpg"
      }
    ],
    evidence: [
      {
        id: "HT-EV-01",
        title: "Chhatri Dome Plinth Erosion",
        feature: "Chhatri Dome Base Masonry",
        confidence: "89%",
        coords: "X: [120, 200], Y: [90, 160]",
        status: "Pending Review",
        algorithm: "Difference Mask (Intensity)",
        cropArchivalOffset: { x: 30, y: 15 },
        cropModernOffset: { x: 32, y: 14 }
      },
      {
        id: "HT-EV-02",
        title: "Facade Sandstone Discoloration",
        feature: "Central Iwan Sandstone Arch",
        confidence: "74%",
        coords: "X: [450, 520], Y: [180, 230]",
        status: "Pending Review",
        algorithm: "Photometric L*a*b Difference",
        cropArchivalOffset: { x: 55, y: 40 },
        cropModernOffset: { x: 56, y: 39 }
      },
      {
        id: "HT-EV-03",
        title: "Encroaching Garden Vegetation",
        feature: "Plinth Ground Interface",
        confidence: "95%",
        coords: "X: [80, 310], Y: [380, 460]",
        status: "Pending Review",
        algorithm: "Green Index Mask (ExG)",
        cropArchivalOffset: { x: 10, y: 80 },
        cropModernOffset: { x: 12, y: 78 }
      },
      {
        id: "HT-EV-04",
        title: "Plinth Arcade Restored Archway",
        feature: "Plinth Arcade Arch #04",
        confidence: "82%",
        coords: "X: [520, 680], Y: [340, 480]",
        status: "Pending Review",
        algorithm: "Structural Similarity Index (SSIM)",
        cropArchivalOffset: { x: 75, y: 75 },
        cropModernOffset: { x: 76, y: 74 }
      }
    ],
    matches: [
      { x1: 150, y1: 120, x2: 152, y2: 119 },
      { x1: 220, y1: 140, x2: 224, y2: 138 },
      { x1: 310, y1: 180, x2: 312, y2: 179 },
      { x1: 450, y1: 190, x2: 455, y2: 189 },
      { x1: 520, y1: 210, x2: 522, y2: 209 },
      { x1: 680, y1: 220, x2: 684, y2: 218 },
      { x1: 180, y1: 340, x2: 182, y2: 338 },
      { x1: 290, y1: 350, x2: 295, y2: 349 },
      { x1: 410, y1: 360, x2: 412, y2: 359 },
      { x1: 610, y1: 370, x2: 615, y2: 368 },
      { x1: 110, y1: 240, x2: 112, y2: 239 },
      { x1: 360, y1: 260, x2: 362, y2: 259 },
      { x1: 490, y1: 270, x2: 494, y2: 268 },
      { x1: 710, y1: 280, x2: 714, y2: 278 }
    ]
  },
  sanchi: {
    name: "Sanchi Stupa / Toranas",
    location: "Madhya Pradesh",
    epochs: "1890 – 2026",
    statusText: "LoFTR FEASIBILITY: HIGHLY SUCCESSFUL",
    statusType: "success",
    metrics: {
      predictedPoints: 720,
      ransacInliers: 215,
      inlierRatio: "58.9%",
      reprojRmse: "~1.45 px",
      facadeAlign: "Valid",
      parallaxGap: "Negligible",
      hMatrix: [
        ["0.91234", "0.00512", "154.215"],
        ["-0.00341", "0.90824", "92.148"],
        ["0.00005", "0.00011", "1.00000"]
      ],
      hCond: "~1.25e4",
      hDet: "0.828",
      hSupport: "91%",
      vSupport: "64%",
      hullCoverage: "12.4%",
      confMean: "88.5%"
    },
    timeline: [
      {
        year: "1890",
        era: "Archival Base",
        stamp: "SS-1890-01",
        title: "Northern Torana Reconstruction",
        desc: "Archival photography from Major Cole's seminal restoration campaign. Captures the stone gateways (Toranas) shortly after re-erection of the collapsed top lintels.",
        author: "Major Henry Cole",
        source: "ASI Archaeological Library",
        license: "Public Domain",
        notes: "High fidelity albumen print. Perfect planar gateway features.",
        img: "assets/sanchi_archival.jpg"
      },
      {
        year: "1920",
        era: "Survey Era",
        stamp: "SS-1920-03",
        title: "Sir John Marshall Survey",
        desc: "Survey plate detailing the hemispherical brick and stone dome structure and the surrounding balustrade. Shows minor mortar washing on the lower dome face.",
        author: "Sir John Marshall Collection",
        source: "British Museum Library",
        license: "Educational Non-Commercial",
        notes: "Gelatin silver glass plate negative. Excellent light balance.",
        img: "assets/sanchi_archival.jpg"
      },
      {
        year: "1956",
        era: "Mid-Century",
        stamp: "SS-1956-01",
        title: "2500th Buddha Jayanti",
        desc: "Historic documentation recording physical wear prior to major Buddhist jubilee assembly. Stone railings show moss growth on the northern quadrant.",
        author: "Mahabodhi Society Commission",
        source: "National Museum New Delhi",
        license: "Public Domain Citation",
        notes: "Pan-chromatic paper print. Moderate grain.",
        img: "assets/sanchi_archival.jpg"
      },
      {
        year: "1989",
        era: "UNESCO Inscription",
        stamp: "SS-1989-02",
        title: "UNESCO Heritage File",
        desc: "Visual plate establishing the site buffer boundaries and core architectural fence condition. Stone surface shows stable weathering patterns.",
        author: "UNESCO World Heritage Centre",
        source: "UNESCO Digital Library",
        license: "Educational Use",
        notes: "Medium format color slide scan.",
        img: "assets/sanchi_modern.jpg"
      },
      {
        year: "2026",
        era: "Contemporary",
        stamp: "SS-2026-04",
        title: "Contemporary Conservation View",
        desc: "Modern digital view matching the 1890 Major Cole camera viewpoint. Provides precise spatial mapping of ancient stone block joint movements.",
        author: "DTHeritage Archival Stack",
        source: "Contemporary Stack",
        license: "Project Custody",
        notes: "Digital RAW file. LoFTR registration confirms 91% horizontal support alignment.",
        img: "assets/sanchi_modern.jpg"
      }
    ],
    evidence: [
      {
        id: "SS-EV-01",
        title: "Torana Architrave Micro-crack",
        feature: "Northern Torana Lintel",
        confidence: "91%",
        coords: "X: [210, 260], Y: [80, 110]",
        status: "Pending Review",
        algorithm: "Structural Similarity Index (SSIM)",
        cropArchivalOffset: { x: 25, y: 15 },
        cropModernOffset: { x: 26, y: 14 }
      },
      {
        id: "SS-EV-02",
        title: "Stone Balustrade Surface Erosion",
        feature: "West Balustrade Slabs",
        confidence: "80%",
        coords: "X: [350, 420], Y: [240, 310]",
        status: "Pending Review",
        algorithm: "Difference Mask (Intensity)",
        cropArchivalOffset: { x: 45, y: 35 },
        cropModernOffset: { x: 46, y: 34 }
      },
      {
        id: "SS-EV-03",
        title: "Stupa Dome Coating Wear",
        feature: "Hemispherical Dome Plaster",
        confidence: "86%",
        coords: "X: [120, 180], Y: [150, 210]",
        status: "Pending Review",
        algorithm: "Photometric L*a*b Difference",
        cropArchivalOffset: { x: 15, y: 20 },
        cropModernOffset: { x: 17, y: 19 }
      }
    ],
    matches: [
      { x1: 180, y1: 100, x2: 181, y2: 99 },
      { x1: 240, y1: 110, x2: 242, y2: 108 },
      { x1: 300, y1: 120, x2: 301, y2: 119 },
      { x1: 380, y1: 130, x2: 382, y2: 128 },
      { x1: 450, y1: 140, x2: 453, y2: 139 },
      { x1: 220, y1: 220, x2: 222, y2: 219 },
      { x1: 280, y1: 230, x2: 282, y2: 229 },
      { x1: 340, y1: 240, x2: 344, y2: 238 },
      { x1: 410, y1: 250, x2: 412, y2: 249 },
      { x1: 130, y1: 320, x2: 132, y2: 319 },
      { x1: 190, y1: 330, x2: 192, y2: 329 },
      { x1: 250, y1: 340, x2: 254, y2: 338 },
      { x1: 310, y1: 350, x2: 312, y2: 349 },
      { x1: 480, y1: 360, x2: 483, y2: 358 }
    ]
  },
  qutb: {
    name: "Qutb Minar Complex",
    location: "Delhi",
    epochs: "1870 – 2026",
    statusText: "LoFTR FEASIBILITY: WARNING (PARALLAX LIMITATIONS)",
    statusType: "warning",
    metrics: {
      predictedPoints: 512,
      ransacInliers: 92,
      inlierRatio: "31.2%",
      reprojRmse: "~2.99 px",
      facadeAlign: "Marginal",
      parallaxGap: "Significant",
      hMatrix: [
        ["0.75124", "-0.04512", "320.124"],
        ["0.03812", "0.72241", "195.421"],
        ["0.00031", "-0.00012", "1.00000"]
      ],
      hCond: "~3.10e4",
      hDet: "0.542",
      hSupport: "68%",
      vSupport: "12%",
      hullCoverage: "2.35%",
      confMean: "71.4%"
    },
    timeline: [
      {
        year: "1870",
        era: "Archival Base",
        stamp: "QM-1870-01",
        title: "Beglar Photographic Plate",
        desc: "Rare archival albumen photograph by J.D. Beglar. Taken from the ruins of the Quwwat-ul-Islam mosque looking upward at the minaret, showing the sandstone balcony details.",
        author: "Joseph David Beglar",
        source: "British Library India Office",
        license: "Public Domain",
        notes: "Extreme upward perspective, severe radial distortion from camera lens.",
        img: "assets/qutb_archival.jpg"
      },
      {
        year: "1910",
        era: "Survey Era",
        stamp: "QM-1910-02",
        title: "ASI Structural Assessment",
        desc: "Detailed record plate detailing the ground-level stone joint fissures and early iron tie rod reinforcements installed to counter tower tilt.",
        author: "Archaeological Survey of India (ASI)",
        source: "ASI Library Archives",
        license: "CC BY Citation",
        notes: "Orthochromatic plate. High contrast, sharp shadow details.",
        img: "assets/qutb_archival.jpg"
      },
      {
        year: "1960",
        era: "Mid-Century",
        stamp: "QM-1960-05",
        title: "Seismic Monitoring Baseline",
        desc: "Documentary photography following regional earthquake tremor. Aligned views of Balcony #02 and Balcony #03 honeycomb carvings were acquired.",
        author: "CSIR Structural Research",
        source: "CSIR Archives India",
        license: "Official Record",
        notes: "Black and white safety film negative.",
        img: "assets/qutb_archival.jpg"
      },
      {
        year: "1993",
        era: "UNESCO Inscription",
        stamp: "QM-1993-01",
        title: "World Heritage Inscription Plate",
        desc: "Visual dossier photograph showing the alignment of the tower to the surrounding stone columns of the mosque courtyard ruins.",
        author: "UNESCO Preservation Team",
        source: "UNESCO World Archives",
        license: "Educational Non-Commercial",
        notes: "Color film scan. Viewpoint matches historical plate.",
        img: "assets/qutb_modern.jpg"
      },
      {
        year: "2026",
        era: "Contemporary",
        stamp: "QM-2026-11",
        title: "UAV Architectural Scan",
        desc: "Modern viewpoint image extracted from a close range UAV photogrammetric dataset. Compensated for severe radial distortion to verify sandstone brick shift.",
        author: "DTHeritage UAV Scan",
        source: "Contemporary Stack",
        license: "Project Custody",
        notes: "Digital CMOS sensor. Ortho-corrected facade alignment.",
        img: "assets/qutb_modern.jpg"
      }
    ],
    evidence: [
      {
        id: "QM-EV-01",
        title: "Balcony Bracket Fissure Candidate",
        feature: "Balcony #02 Red Sandstone Bracket",
        confidence: "68%",
        coords: "X: [180, 240], Y: [220, 280]",
        status: "Pending Review",
        algorithm: "Structural Similarity Index (SSIM)",
        cropArchivalOffset: { x: 20, y: 35 },
        cropModernOffset: { x: 21, y: 34 }
      },
      {
        id: "QM-EV-02",
        title: "Minaret Tilt Parallax Discrepancy",
        feature: "Upper Fluted Columns Alignment",
        confidence: "55%",
        coords: "X: [290, 360], Y: [410, 480]",
        status: "Pending Review",
        algorithm: "Difference Mask (Intensity)",
        cropArchivalOffset: { x: 38, y: 65 },
        cropModernOffset: { x: 37, y: 64 }
      }
    ],
    matches: [
      { x1: 250, y1: 180, x2: 248, y2: 179 },
      { x1: 290, y1: 210, x2: 288, y2: 209 },
      { x1: 320, y1: 240, x2: 318, y2: 239 },
      { x1: 340, y1: 280, x2: 338, y2: 279 },
      { x1: 220, y1: 310, x2: 219, y2: 309 },
      { x1: 270, y1: 350, x2: 269, y2: 349 },
      { x1: 310, y1: 390, x2: 309, y2: 389 },
      { x1: 330, y1: 430, x2: 329, y2: 429 }
    ]
  }
};

// Replace the original design mock values with the verified curated records.
// Generated CV output is intentionally not inferred here: it will be loaded only
// once the versioned output bundle is available.
Object.assign(monumentsData.humayun, {
  epochs: "1858–2015",
  statusText: "LOFTR BASELINE: FACADE VALIDATED",
  statusType: "success",
  metrics: {
    predictedPoints: 658, ransacInliers: 182, inlierRatio: "52.8%", reprojRmse: "1.67 px",
    facadeAlign: "Facade only", parallaxGap: "Dome / ground limited",
    hMatrix: [["0.84221", "-0.01254", "241.521"], ["0.01524", "0.83548", "108.204"], ["0.00012", "0.00021", "1.00000"]],
    hCond: "1.90e4", hDet: "Not recorded", hSupport: "Not recorded", vSupport: "18%", hullCoverage: "5.18%", confMean: "Not recorded"
  },
  timeline: [
    { year: "1858", era: "Archival Reference", stamp: "HUM-H02", title: "Humayun's Tomb, Side Garden", desc: "Curated archival reference image from the project dataset.", author: "Felice Beato", source: "Wellcome Collection", license: "Public Domain", notes: "Side-garden viewpoint; not presented as a registered comparison result.", img: "assets/humayun_archival.jpg" },
    { year: "1860", era: "Archival Baseline", stamp: "HUM-H01", title: "Humayun's Tomb, Delhi", desc: "Curated historical reference for the documented LoFTR baseline.", author: "John Edward Saché", source: "Wikimedia Commons / British Library", license: "Public Domain", notes: "Front/main facade; uncalibrated archival photograph.", img: "assets/humayun_archival.jpg" },
    { year: "2015", era: "Contemporary Reference", stamp: "HUM-M03", title: "Humayun's Tomb, Front View", desc: "Curated contemporary reference image from the project dataset.", author: "ManishKS12", source: "Wikimedia Commons", license: "CC BY-SA 4.0", notes: "The documented LoFTR result is valid on the main facade only.", img: "assets/humayun_modern.jpg" }
  ],
  evidence: [], matches: []
});

Object.assign(monumentsData.sanchi, {
  epochs: "1863–2017", statusText: "REGISTRATION OUTPUT AWAITING VERIFICATION", statusType: "warning",
  metrics: { predictedPoints: "—", ransacInliers: "—", inlierRatio: "Not available", reprojRmse: "Not available", facadeAlign: "Not verified", parallaxGap: "Not verified", hMatrix: [["—", "—", "—"], ["—", "—", "—"], ["—", "—", "—"]], hCond: "Not available", hDet: "Not available", hSupport: "Not available", vSupport: "Not available", hullCoverage: "Not available", confMean: "Not available" },
  timeline: [
    { year: "1863", era: "Archival Reference", stamp: "SAN-H01", title: "Eastern Gateway / Torana", desc: "Curated archival reference image from the project dataset.", author: "James John Waterhouse", source: "Rijksmuseum", license: "Public Domain", notes: "Front view of the eastern gateway.", img: "assets/sanchi_archival.jpg" },
    { year: "1880", era: "Archival Reference", stamp: "SAN-H02", title: "Sanchi Stupa, Side View", desc: "Additional curated archival reference image.", author: "Unknown", source: "British Museum", license: "CC BY-NC-SA 4.0", notes: "Side view.", img: "assets/sanchi_archival.jpg" },
    { year: "2015", era: "Contemporary Reference", stamp: "SAN-M01", title: "Eastern Gateway / Torana", desc: "Curated contemporary reference image from the project dataset.", author: "Unknown", source: "TripInvites", license: "License needs confirmation", notes: "Front view; shown as source material, not a validated registration.", img: "assets/sanchi_modern.jpg" },
    { year: "2017", era: "Contemporary Reference", stamp: "SAN-M02", title: "Sanchi Stupa, Side View", desc: "Curated contemporary reference image from the project dataset.", author: "Anandajoti Bhikkhu", source: "Wikimedia Commons", license: "Public Domain", notes: "Side view.", img: "assets/sanchi_modern.jpg" }
  ], evidence: [], matches: []
});

Object.assign(monumentsData.qutb, {
  epochs: "1858–2017", statusText: "REGISTRATION OUTPUT AWAITING VERIFICATION", statusType: "warning",
  metrics: { predictedPoints: "—", ransacInliers: "—", inlierRatio: "Not available", reprojRmse: "Not available", facadeAlign: "Not verified", parallaxGap: "Not verified", hMatrix: [["—", "—", "—"], ["—", "—", "—"], ["—", "—", "—"]], hCond: "Not available", hDet: "Not available", hSupport: "Not available", vSupport: "Not available", hullCoverage: "Not available", confMean: "Not available" },
  timeline: [
    { year: "1858", era: "Archival Reference", stamp: "QUT-H01", title: "Qutb Minar, Full-height View", desc: "Curated archival reference image from the project dataset.", author: "Unknown", source: "Wikimedia Commons", license: "CC0 1.0", notes: "Full-height vertical view.", img: "assets/qutb_archival.jpg" },
    { year: "1860", era: "Archival Reference", stamp: "QUT-H02", title: "Qutb Minar, Decorative Detail", desc: "Curated archival reference image from the project dataset.", author: "Samuel Bourne", source: "Wikimedia Commons", license: "Public Domain", notes: "Closer decorative-elements view.", img: "assets/qutb_archival.jpg" },
    { year: "2008", era: "Contemporary Reference", stamp: "QUT-M01", title: "Qutb Minar Tower", desc: "Curated contemporary reference image from the project dataset.", author: "Ondřej Žváček", source: "Wikipedia", license: "GFDL / CC BY-SA", notes: "Vertical/full view.", img: "assets/qutb_modern.jpg" },
    { year: "2017", era: "Contemporary Reference", stamp: "QUT-M04", title: "Qutb Minar, Full View", desc: "Curated contemporary reference image from the project dataset.", author: "Pragyanand Raushan", source: "Wikimedia Commons", license: "CC BY-SA 4.0", notes: "South-side full view.", img: "assets/qutb_modern.jpg" }
  ], evidence: [], matches: []
});

// Global App State
let activeView = 'portfolio';
let activeMonument = 'humayun';
let activeTimelineIndex = 0;
let activeComparisonMode = 'sbs';
let showLoftrOverlay = false;
let activeEvidenceId = '';

function formatMatrix(matrix) {
  return matrix.map(row => row.map(value => Number(value).toPrecision(5)));
}

function evidenceForUi(candidate, index) {
  const [x, y, width, height] = candidate.bbox_xywh_in_inference_image || candidate.bbox_xywh;
  return {
    id: candidate.candidate_id,
    title: `Candidate visual difference #${index + 1}`,
    feature: candidate.registration_region_label,
    confidence: candidate.evidence_strength.replace('_', ' ').toLowerCase(),
    coords: `X: [${x}, ${x + width}], Y: [${y}, ${y + height}]`,
    status: candidate.review_status === 'PENDING_REVIEW' ? 'Pending Review' : candidate.review_status,
    algorithm: 'Histogram-normalized intensity, gradient, and edge signals',
    cropArchivalOffset: { x: (x / 840) * 100, y: (y / 560) * 100 },
    cropModernOffset: { x: (x / 840) * 100, y: (y / 560) * 100 },
    uncertainty: candidate.uncertainty_indicators.join('; ') || 'No additional indicator recorded'
  };
}

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

  const base = `data/verification/${monumentId}/`;
  const [metrics, evidence] = await Promise.all(files.map(file => fetch(base + file).then(response => {
    if (!response.ok) throw new Error(`Unable to load ${file}`);
    return response.json();
  })));
  return { metrics, evidence };
}

async function loadVerificationBundle() {
  const sources = {
    humayun: ['registration_metrics_pair02.json', 'candidate_evidence.json'],
    sanchi: ['registration_metrics_gateway.json', 'candidate_evidence.json'],
    qutb: ['registration_metrics_full_height.json', 'candidate_evidence.json']
  };
  try {
    await Promise.all(Object.entries(sources).map(async ([monumentId, files]) => {
      const { metrics, evidence } = await loadVerificationData(monumentId, files);
      const ransac = metrics.ransac || {};
      const geometry = (metrics.geometric_error || {}).over_ransac_inliers || {};
      const homography = metrics.homography || {};
      const valid = metrics.status === 'success';
      Object.assign(monumentsData[monumentId].metrics, {
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
      });
      monumentsData[monumentId].evidence = (evidence.candidates || []).map(evidenceForUi);
      monumentsData[monumentId].statusText = valid
        ? 'BOUNDED REGISTRATION: CHANGE EVIDENCE VIABLE'
        : 'REGISTRATION REJECTED: NO CHANGE EVIDENCE';
      monumentsData[monumentId].statusType = valid ? 'success' : 'warning';
    }));
    updatePortfolioTable();
    document.querySelector('.hero-photo-caption').textContent = "Humayun's Tomb, Delhi · 1860 · Wikimedia Commons / British Library";
    document.querySelector('.hero-photo-wrapper .accession-stamp').textContent = 'HUM-H01';
    loadMonument(activeMonument);
    updateDashboardCounts();
  } catch (error) {
    console.warn('Verification data could not be loaded. Serve this static folder through a local web server to enable the JSON bundle.', error);
  }
}

function updatePortfolioTable() {
  const body = document.querySelector('#portfolio-view .archival-table tbody');
  if (!body) return;
  const catalog = { humayun: '#HT-DEL-01', sanchi: '#SS-MP-02', qutb: '#QM-DEL-03' };
  body.innerHTML = Object.entries(monumentsData).map(([id, data]) => {
    const isValid = data.metrics.facadeAlign !== 'Not validated';
    const result = isValid
      ? `${data.metrics.ransacInliers} Inliers (${data.metrics.inlierRatio} ratio)`
      : `${data.metrics.ransacInliers} Inliers — rejected`;
    const label = isValid ? 'Bounded registration viable' : 'Registration not validated';
    return `<tr style="cursor: pointer;" onclick="loadMonument('${id}')">
      <td>${catalog[id]}</td><td class="monument-name">${data.name}</td><td>${data.location}</td>
      <td>${data.epochs}</td><td>${result}</td>
      <td><span class="badge badge-${data.statusType === 'success' ? 'success' : 'warning'}">${label}</span></td>
      <td><button class="btn btn-sm btn-outline" onclick="loadMonument('${id}'); event.stopPropagation();">Inspect</button></td>
    </tr>`;
  }).join('');
}

// DOM Elements
const views = document.querySelectorAll('.view-container');
const navItems = document.querySelectorAll('.nav-item');
const pageTitle = document.getElementById('page-title');
const pageSubtitle = document.getElementById('page-subtitle');
const monumentSelect = document.getElementById('monument-select');
const globalMonumentSelectorContainer = document.getElementById('global-monument-selector-container');

// Timeline Elements
const timelineMonumentName = document.getElementById('timeline-monument-name');
const timelinePhotoEl = document.getElementById('timeline-photo-el');
const timelineProgress = document.getElementById('timeline-progress');
const timelineRecordStamp = document.getElementById('timeline-record-stamp');
const timelineRecordTitle = document.getElementById('timeline-record-title');
const timelineRecordDesc = document.getElementById('timeline-record-desc');
const timelineMetaAuthor = document.getElementById('timeline-meta-author');
const timelineMetaDate = document.getElementById('timeline-meta-date');
const timelineMetaSource = document.getElementById('timeline-meta-source');
const timelineMetaLicense = document.getElementById('timeline-meta-license');
const timelineMetaNotes = document.getElementById('timeline-meta-notes');

// Comparison Elements
const panelSbs = document.getElementById('panel-sbs');
const panelOverlay = document.getElementById('panel-overlay');
const compImgLeft = document.getElementById('comp-img-left');
const compImgRight = document.getElementById('comp-img-right');
const compImgOverlayBase = document.getElementById('comp-img-overlay-base');
const compImgOverlayTop = document.getElementById('comp-img-overlay-top');
const sliderDragHandle = document.getElementById('slider-drag-handle');
const loftrCanvas = document.getElementById('loftr-canvas');

// Diagnostics & Review Elements
const evidenceQueueList = document.getElementById('evidence-queue-list');
const evidenceDetailPanel = document.getElementById('evidence-detail-panel');
const reclassifyInputBlock = document.getElementById('reclassify-input-block');
const annotationInput = document.getElementById('annotation-input');

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupMonumentSelection();
  setupOverlaySlider();
  
  // Initial Loads
  loadMonument(activeMonument);
  loadVerificationBundle();
  
  // Handle resize for LoFTR canvas
  window.addEventListener('resize', () => {
    if (showLoftrOverlay && activeView === 'comparison') {
      drawLoFTRMatches();
    }
  });
});

// Navigation Setup
function setupNavigation() {
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const target = item.getAttribute('data-target');
      switchView(target);
    });
  });
}

function switchView(target) {
  activeView = target;
  
  // Toggle Navigation Link Classes
  navItems.forEach(nav => {
    if (nav.getAttribute('data-target') === target) {
      nav.classList.add('active');
    } else {
      nav.classList.remove('active');
    }
  });
  
  // Toggle Views Visibility
  views.forEach(view => {
    if (view.getAttribute('id') === `${target}-view`) {
      view.classList.add('active');
    } else {
      view.classList.remove('active');
    }
  });
  
  // Show/Hide Global Monument Selector
  if (target === 'portfolio' || target === 'provenance') {
    globalMonumentSelectorContainer.style.display = 'none';
  } else {
    globalMonumentSelectorContainer.style.display = 'flex';
  }
  
  // Update Header Banner Text
  updateHeaderBanner(target);
  
  // Special view triggers
  if (target === 'comparison' && showLoftrOverlay) {
    setTimeout(drawLoFTRMatches, 100);
  }
}

function updateHeaderBanner(view) {
  const titles = {
    portfolio: {
      title: "Conservation Intelligence",
      subtitle: "A digital archive of India's changing heritage structures."
    },
    timeline: {
      title: "Monument Archives & Timeline",
      subtitle: "Explore chronological architectural visual plates and restorations."
    },
    comparison: {
      title: "Archival & Modern Comparison",
      subtitle: "Interactive spatial alignment, registration, and delta analysis."
    },
    registration: {
      title: "LoFTR Geometric Diagnostics",
      subtitle: "Scientific verification metrics, homography estimation, and coordinate mappings."
    },
    review: {
      title: "Candidate Change Review Queue",
      subtitle: "Manually verify difference anomalies with expert human-in-the-loop oversight."
    },
    provenance: {
      title: "Provenance Registry & Uncertainty Ledger",
      subtitle: "Auditable photographic citations and error distribution parameters."
    }
  };
  
  pageTitle.textContent = titles[view].title;
  pageSubtitle.textContent = titles[view].subtitle;
}

// Monument Selection Setup
function setupMonumentSelection() {
  monumentSelect.addEventListener('change', (e) => {
    loadMonument(e.target.value);
  });
}

function loadMonument(monumentId) {
  activeMonument = monumentId;
  monumentSelect.value = monumentId;
  
  const data = monumentsData[monumentId];
  
  // Update Header Pill
  const statusPill = document.querySelector('.hero-status-pill');
  statusPill.className = `hero-status-pill`;
  
  const statusDot = statusPill.querySelector('.status-dot');
  statusDot.className = `status-dot ${data.statusType}`;
  statusPill.querySelector('span:last-child').textContent = data.statusText.toUpperCase();
  
  // Update Timeline View components
  timelineMonumentName.textContent = `${data.name} — Archival Timeline`;
  setupTimelineTicks(data.timeline);
  setTimelineIndex(0); // reset to first archival image
  
  // Update Comparison View Images and Stats
  compImgLeft.src = data.timeline[0].img;
  compImgRight.src = data.timeline[data.timeline.length - 1].img;
  compImgOverlayTop.src = data.timeline[0].img;
  compImgOverlayBase.src = data.timeline[data.timeline.length - 1].img;
  
  document.getElementById('comp-inlier-ratio').textContent = data.metrics.inlierRatio;
  document.getElementById('comp-predicted-pts').textContent = data.metrics.predictedPoints;
  document.getElementById('comp-ransac-inliers').textContent = data.metrics.ransacInliers;
  document.getElementById('comp-reproj-rmse').textContent = data.metrics.reprojRmse;
  document.getElementById('comp-facade-align').textContent = data.metrics.facadeAlign;
  document.getElementById('comp-parallax-gap').textContent = data.metrics.parallaxGap;
  
  // Update Registration Diagnostics Views
  document.getElementById('h-row-0').children[0].textContent = data.metrics.hMatrix[0][0];
  document.getElementById('h-row-0').children[1].textContent = data.metrics.hMatrix[0][1];
  document.getElementById('h-row-0').children[2].textContent = data.metrics.hMatrix[0][2];
  
  document.getElementById('h-row-1').children[0].textContent = data.metrics.hMatrix[1][0];
  document.getElementById('h-row-1').children[1].textContent = data.metrics.hMatrix[1][1];
  document.getElementById('h-row-1').children[2].textContent = data.metrics.hMatrix[1][2];
  
  document.getElementById('h-row-2').children[0].textContent = data.metrics.hMatrix[2][0];
  document.getElementById('h-row-2').children[1].textContent = data.metrics.hMatrix[2][1];
  document.getElementById('h-row-2').children[2].textContent = data.metrics.hMatrix[2][2];
  
  document.getElementById('h-cond').textContent = data.metrics.hCond;
  document.getElementById('h-det').textContent = data.metrics.hDet;
  
  // Diagnostic bars
  document.getElementById('stat-h-support').textContent = data.metrics.hSupport;
  document.getElementById('bar-h-support').style.width = data.metrics.hSupport;
  document.getElementById('stat-v-support').textContent = data.metrics.vSupport;
  document.getElementById('bar-v-support').style.width = data.metrics.vSupport;
  document.getElementById('stat-hull-coverage').textContent = data.metrics.hullCoverage;
  document.getElementById('bar-hull-coverage').style.width = parseFloat(data.metrics.hullCoverage)*10 + "%"; // scale for visual representation
  document.getElementById('stat-conf-mean').textContent = data.metrics.confMean;
  document.getElementById('bar-conf-mean').style.width = data.metrics.confMean;
  
  // Populate Candidate Change Sidebars & Evidence Reviews
  populateCandidateSidebarList(data.evidence);
  populateEvidenceReviewQueue(data.evidence);
  
  // Populate Provenance Ledger Table
  populateProvenanceTable();
  
  // Reset LoFTR Canvas if showing
  if (showLoftrOverlay && activeView === 'comparison') {
    setTimeout(drawLoFTRMatches, 100);
  }
}

// Timeline Logic
function setupTimelineTicks(timelineList) {
  const ticks = document.querySelectorAll('.timeline-ticks .timeline-tick-node');
  ticks.forEach((tick, idx) => {
    const yearLabel = tick.querySelector('.timeline-tick-label');
    const descLabel = tick.querySelector('.timeline-tick-desc');
    
    if (timelineList[idx]) {
      yearLabel.textContent = timelineList[idx].year;
      descLabel.textContent = timelineList[idx].era;
      tick.style.display = 'block';
    } else {
      tick.style.display = 'none';
    }
  });
}

function setTimelineIndex(index) {
  activeTimelineIndex = index;
  const data = monumentsData[activeMonument];
  const record = data.timeline[index];
  
  // Update Ticks Classes
  const ticks = document.querySelectorAll('.timeline-ticks .timeline-tick-node');
  ticks.forEach((tick, idx) => {
    if (idx === index) {
      tick.classList.add('active');
    } else {
      tick.classList.remove('active');
    }
  });
  
  // Update Progress Bar Width
  const progressPercent = (index / (data.timeline.length - 1)) * 100;
  timelineProgress.style.width = `${progressPercent}%`;
  
  // Update Timeline Details Card
  timelinePhotoEl.src = record.img;
  timelineRecordStamp.textContent = record.stamp;
  timelineRecordTitle.textContent = record.title;
  timelineRecordDesc.textContent = record.desc;
  timelineMetaAuthor.textContent = record.author;
  timelineMetaDate.textContent = record.year === '2026' ? 'Year 2026' : `Circa ${record.year}`;
  timelineMetaSource.textContent = record.source;
  timelineMetaLicense.textContent = record.license;
  timelineMetaNotes.textContent = record.notes;
}

// Image Comparison Overlay Slider setup
function setupOverlaySlider() {
  let isDragging = false;
  
  sliderDragHandle.addEventListener('mousedown', (e) => {
    isDragging = true;
    e.preventDefault();
  });
  
  window.addEventListener('mouseup', () => {
    isDragging = false;
  });
  
  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    updateSlider(e.clientX);
  });
  
  // Touch support
  sliderDragHandle.addEventListener('touchstart', (e) => {
    isDragging = true;
    e.preventDefault();
  });
  window.addEventListener('touchend', () => {
    isDragging = false;
  });
  window.addEventListener('touchmove', (e) => {
    if (!isDragging) return;
    updateSlider(e.touches[0].clientX);
  });
}

function updateSlider(clientX) {
  const viewerRect = document.getElementById('comparison-viewer').getBoundingClientRect();
  let offset = clientX - viewerRect.left;
  
  if (offset < 0) offset = 0;
  if (offset > viewerRect.width) offset = viewerRect.width;
  
  const percentage = (offset / viewerRect.width) * 100;
  sliderDragHandle.style.left = `${percentage}%`;
  compImgOverlayTop.style.clipPath = `inset(0 ${100 - percentage}% 0 0)`;
}

function setComparisonMode(mode) {
  activeComparisonMode = mode;
  document.getElementById('btn-mode-sbs').classList.toggle('active', mode === 'sbs');
  document.getElementById('btn-mode-overlay').classList.toggle('active', mode === 'overlay');
  
  panelSbs.style.display = mode === 'sbs' ? 'grid' : 'none';
  panelOverlay.style.display = mode === 'overlay' ? 'block' : 'none';
  
  // Re-render canvas matches if toggled
  if (showLoftrOverlay) {
    drawLoFTRMatches();
  }
}

// LoFTR Matches Canvas Overlay Logic
function toggleLoFTRMatches(checked) {
  showLoftrOverlay = checked;
  loftrCanvas.classList.toggle('active', checked);
  
  if (checked) {
    drawLoFTRMatches();
  }
}

function drawLoFTRMatches() {
  const ctx = loftrCanvas.getContext('2d');
  const frame = document.getElementById('comparison-viewer');
  
  // Reset Dimensions to match current frame layout size
  const width = frame.clientWidth;
  const height = frame.clientHeight;
  loftrCanvas.width = width;
  loftrCanvas.height = height;
  
  ctx.clearRect(0, 0, width, height);
  
  const data = monumentsData[activeMonument];
  if (!data.matches) return;
  
  if (activeComparisonMode === 'sbs') {
    // Side by side matching lines
    const halfWidth = width / 2;
    data.matches.forEach(match => {
      // Map coordinates to left image bounding box
      const x1 = (match.x1 / 800) * halfWidth;
      const y1 = (match.y1 / 500) * height;
      
      // Map coordinates to right image bounding box
      const x2 = halfWidth + ((match.x2 / 800) * halfWidth);
      const y2 = (match.y2 / 500) * height;
      
      // Draw Line
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = 'rgba(166, 95, 67, 0.45)'; // Terracotta
      ctx.lineWidth = 1;
      ctx.stroke();
      
      // Draw dots
      ctx.beginPath();
      ctx.arc(x1, y1, 2.5, 0, 2 * Math.PI);
      ctx.fillStyle = '#B08A57'; // Muted brass
      ctx.fill();
      
      ctx.beginPath();
      ctx.arc(x2, y2, 2.5, 0, 2 * Math.PI);
      ctx.fillStyle = '#A65F43'; // Terracotta
      ctx.fill();
    });
  } else {
    // Overlay matching nodes
    data.matches.forEach(match => {
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

// Sidebars & Queues Populations
function populateCandidateSidebarList(evidenceList) {
  const sidebarContainer = document.getElementById('candidate-changes-sidebar');
  sidebarContainer.innerHTML = '';
  if (!evidenceList.length) {
    sidebarContainer.innerHTML = '<div class="change-item-sidebar"><div class="change-item-desc"><span class="change-item-name">No verified candidate evidence</span><span class="change-item-meta">Awaiting the versioned CV output bundle.</span></div></div>';
    return;
  }
  
  evidenceList.forEach((ev, idx) => {
    const item = document.createElement('div');
    item.className = `change-item-sidebar ${idx === 0 ? 'active' : ''}`;
    item.setAttribute('data-id', ev.id);
    item.onclick = () => {
      // Highlight selection in comparison screen
      document.querySelectorAll('.change-item-sidebar').forEach(el => el.classList.remove('active'));
      item.classList.add('active');
      
      // Switch to review queue screen and focus
      switchView('review');
      loadEvidenceItem(ev.id);
    };
    
    item.innerHTML = `
      <div class="change-item-desc">
        <span class="change-item-name">${ev.title}</span>
        <span class="change-item-meta">${ev.feature} · Conf: ${ev.confidence}</span>
      </div>
      <div>
        <span class="status-dot ${ev.status === 'Accepted' ? 'success' : (ev.status === 'Rejected' ? 'error' : 'warning')}"></span>
      </div>
    `;
    sidebarContainer.appendChild(item);
  });
}

function populateEvidenceReviewQueue(evidenceList) {
  evidenceQueueList.innerHTML = '';
  if (!evidenceList.length) {
    evidenceQueueList.innerHTML = '<div class="evidence-row-card"><div class="evidence-row-left"><span class="evidence-row-title">No verified candidate evidence</span><span class="evidence-row-meta">Candidate evidence will appear after validated output JSON is supplied.</span></div></div>';
    return;
  }
  
  evidenceList.forEach((ev, idx) => {
    const card = document.createElement('div');
    const isPending = ev.status === 'Pending Review' || ev.status.startsWith('Pending');
    const isAccepted = ev.status === 'Accepted';
    const isRejected = ev.status === 'Rejected';
    
    card.className = `evidence-row-card ${idx === 0 ? 'active' : ''} ${!isPending ? 'reviewed' : ''}`;
    card.setAttribute('id', `queue-card-${ev.id}`);
    card.onclick = () => {
      document.querySelectorAll('.evidence-row-card').forEach(el => el.classList.remove('active'));
      card.classList.add('active');
      loadEvidenceItem(ev.id);
    };
    
    let badgeClass = 'badge-warning';
    if (isAccepted) badgeClass = 'badge-success';
    if (isRejected) badgeClass = 'badge-error';
    
    card.innerHTML = `
      <div class="evidence-row-left">
        <span class="evidence-row-title">${ev.title}</span>
        <span class="evidence-row-meta">${ev.feature} · Coordinates: ${ev.coords}</span>
      </div>
      <div class="evidence-row-right">
        <span class="evidence-row-confidence">${ev.confidence} Conf.</span>
        <span class="badge ${badgeClass}" id="badge-status-${ev.id}">${ev.status}</span>
      </div>
    `;
    evidenceQueueList.appendChild(card);
    
    if (idx === 0) {
      loadEvidenceItem(ev.id);
    }
  });
}

// Load focused evidence review details on the right card panel
function loadEvidenceItem(evId) {
  activeEvidenceId = evId;
  const data = monumentsData[activeMonument];
  const ev = data.evidence.find(item => item.id === evId);
  
  document.getElementById('detail-ev-id').textContent = ev.id;
  document.getElementById('detail-ev-title').textContent = ev.title;
  document.getElementById('detail-ev-algorithm').textContent = ev.algorithm;
  document.getElementById('detail-ev-confidence').textContent = ev.confidence;
  document.getElementById('detail-ev-coords').textContent = ev.coords;
  document.getElementById('detail-ev-feature').textContent = ev.feature;
  
  // Images
  const archivalImg = document.getElementById('detail-crop-archival');
  const modernImg = document.getElementById('detail-crop-modern');
  
  archivalImg.src = data.timeline[0].img;
  modernImg.src = data.timeline[data.timeline.length - 1].img;
  
  // Set highlight crop offsets
  const archivalBox = document.getElementById('detail-crop-box-archival');
  const modernBox = document.getElementById('detail-crop-box-modern');
  
  archivalBox.style.left = `${ev.cropArchivalOffset.x}%`;
  archivalBox.style.top = `${ev.cropArchivalOffset.y}%`;
  archivalBox.style.width = '20%';
  archivalBox.style.height = '25%';
  
  modernBox.style.left = `${ev.cropModernOffset.x}%`;
  modernBox.style.top = `${ev.cropModernOffset.y}%`;
  modernBox.style.width = '20%';
  modernBox.style.height = '25%';
  
  // Status tag
  const statusVal = document.getElementById('detail-ev-status');
  const isPending = ev.status === 'Pending Review' || ev.status.startsWith('Pending');
  const isAccepted = ev.status === 'Accepted';
  const isRejected = ev.status === 'Rejected';
  
  if (isAccepted) {
    statusVal.innerHTML = `<span class="badge badge-success">Accepted</span>`;
  } else if (isRejected) {
    statusVal.innerHTML = `<span class="badge badge-error">Rejected</span>`;
  } else {
    statusVal.innerHTML = `<span class="badge badge-warning">${ev.status}</span>`;
  }
  
  // Progress bar
  document.getElementById('detail-ev-bar-percent').textContent = ev.confidence;
  document.getElementById('detail-ev-bar-fill').style.width = ev.confidence;
  
  // Hide annotation panel by default
  reclassifyInputBlock.style.display = 'none';
  annotationInput.value = '';
}

// Action Button triggers for evidence review
function reviewAction(action) {
  const data = monumentsData[activeMonument];
  const ev = data.evidence.find(item => item.id === activeEvidenceId);
  if (!ev) return;
  const card = document.getElementById(`queue-card-${activeEvidenceId}`);
  const badge = document.getElementById(`badge-status-${activeEvidenceId}`);
  
  if (action === 'accept') {
    ev.status = 'Accepted';
    evidenceDetailPanel.classList.remove('glow-error');
    evidenceDetailPanel.classList.add('glow-success');
    setTimeout(() => evidenceDetailPanel.classList.remove('glow-success'), 500);
    
    badge.className = 'badge badge-success';
    badge.textContent = 'Accepted';
    card.classList.add('reviewed');
    
    loadEvidenceItem(activeEvidenceId);
    
  } else if (action === 'reject') {
    ev.status = 'Rejected';
    evidenceDetailPanel.classList.remove('glow-success');
    evidenceDetailPanel.classList.add('glow-error');
    setTimeout(() => evidenceDetailPanel.classList.remove('glow-error'), 500);
    
    badge.className = 'badge badge-error';
    badge.textContent = 'Rejected';
    card.classList.add('reviewed');
    
    loadEvidenceItem(activeEvidenceId);
    
  } else if (action === 'reclassify') {
    reclassifyInputBlock.style.display = 'block';
    annotationInput.focus();
  }
  
  // Refresh sidebars and status logs
  populateCandidateSidebarList(data.evidence);
  updateDashboardCounts();
}

function saveAnnotation() {
  const data = monumentsData[activeMonument];
  const ev = data.evidence.find(item => item.id === activeEvidenceId);
  if (!ev) return;
  const notes = annotationInput.value.trim();
  
  if (notes) {
    ev.status = `Reclassified: ${notes}`;
    const badge = document.getElementById(`badge-status-${activeEvidenceId}`);
    badge.className = 'badge badge-warning';
    badge.textContent = 'Reclassified';
    
    loadEvidenceItem(activeEvidenceId);
    reclassifyInputBlock.style.display = 'none';
    
    // Refresh sidebars
    populateCandidateSidebarList(data.evidence);
    updateDashboardCounts();
  }
}

function updateDashboardCounts() {
  // Compute verified review availability across the curated records.
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
  
  // Update dashboard labels if active
  const dashboard = document.getElementById('portfolio-view');
  if (dashboard) {
    const boxes = dashboard.querySelectorAll('.hero-stat-box');
    boxes[2].querySelector('.hero-stat-val').innerHTML = `${String(totalReviewed).padStart(2, '0')}`;
    boxes[3].querySelector('.hero-stat-val').innerHTML = `${String(totalPending).padStart(2, '0')} <span>available</span>`;
  }
}

// Populate Provenance Ledger table on screen 6
function populateProvenanceTable() {
  const tableBody = document.getElementById('provenance-table-body');
  tableBody.innerHTML = '';
  
  Object.keys(monumentsData).forEach(monId => {
    const data = monumentsData[monId];
    data.timeline.forEach(record => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td style="font-family:monospace; font-weight:600; color:var(--accent-rose);">${record.stamp}</td>
        <td style="font-family:var(--font-serif); font-size:1rem; font-weight:600;">${data.name}</td>
        <td>${record.source}</td>
        <td>${record.year}</td>
        <td>${record.author}</td>
        <td><span class="badge ${record.license === 'Public Domain' ? 'badge-success' : 'badge-warning'}" style="font-size:0.65rem;">${record.license}</span></td>
      `;
      tableBody.appendChild(row);
    });
  });
}

// Diagnostic manual alignment simulator
function simulateManualAlignment() {
  alert("Manual landmark alignment is a planned human-in-the-loop workflow. This static UI does not fabricate a registration result; use validated landmark output when it is available.");
}
