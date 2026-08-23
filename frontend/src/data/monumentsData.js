// Ported verbatim from the vanilla app.js data model.
// Values are unchanged from the original; only image paths were made
// root-absolute ("/assets/...") to work correctly with Vite's public/ dir.

export function createInitialMonumentsData() {
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
          img: "/assets/humayun_archival.jpg"
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
          img: "/assets/humayun_archival.jpg"
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
          img: "/assets/humayun_archival.jpg"
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
          img: "/assets/humayun_modern.jpg"
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
          img: "/assets/humayun_modern.jpg"
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
          img: "/assets/sanchi_archival.jpg"
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
          img: "/assets/sanchi_archival.jpg"
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
          img: "/assets/sanchi_archival.jpg"
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
          img: "/assets/sanchi_modern.jpg"
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
          img: "/assets/sanchi_modern.jpg"
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
          img: "/assets/qutb_archival.jpg"
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
          img: "/assets/qutb_archival.jpg"
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
          img: "/assets/qutb_archival.jpg"
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
          img: "/assets/qutb_modern.jpg"
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
          img: "/assets/qutb_modern.jpg"
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
      { year: "1858", era: "Archival Reference", stamp: "HUM-H02", title: "Humayun's Tomb, Side Garden", desc: "Curated archival reference image from the project dataset.", author: "Felice Beato", source: "Wellcome Collection", license: "Public Domain", notes: "Side-garden viewpoint; not presented as a registered comparison result.", img: "/assets/humayun_archival.jpg" },
      { year: "1860", era: "Archival Baseline", stamp: "HUM-H01", title: "Humayun's Tomb, Delhi", desc: "Curated historical reference for the documented LoFTR baseline.", author: "John Edward Saché", source: "Wikimedia Commons / British Library", license: "Public Domain", notes: "Front/main facade; uncalibrated archival photograph.", img: "/assets/humayun_archival.jpg" },
      { year: "2015", era: "Contemporary Reference", stamp: "HUM-M03", title: "Humayun's Tomb, Front View", desc: "Curated contemporary reference image from the project dataset.", author: "ManishKS12", source: "Wikimedia Commons", license: "CC BY-SA 4.0", notes: "The documented LoFTR result is valid on the main facade only.", img: "/assets/humayun_modern.jpg" }
    ],
    evidence: [], matches: []
  });

  Object.assign(monumentsData.sanchi, {
    epochs: "1863–2017", statusText: "REGISTRATION OUTPUT AWAITING VERIFICATION", statusType: "warning",
    metrics: { predictedPoints: "—", ransacInliers: "—", inlierRatio: "Not available", reprojRmse: "Not available", facadeAlign: "Not verified", parallaxGap: "Not verified", hMatrix: [["—", "—", "—"], ["—", "—", "—"], ["—", "—", "—"]], hCond: "Not available", hDet: "Not available", hSupport: "Not available", vSupport: "Not available", hullCoverage: "Not available", confMean: "Not available" },
    timeline: [
      { year: "1863", era: "Archival Reference", stamp: "SAN-H01", title: "Eastern Gateway / Torana", desc: "Curated archival reference image from the project dataset.", author: "James John Waterhouse", source: "Rijksmuseum", license: "Public Domain", notes: "Front view of the eastern gateway.", img: "/assets/sanchi_archival.jpg" },
      { year: "1880", era: "Archival Reference", stamp: "SAN-H02", title: "Sanchi Stupa, Side View", desc: "Additional curated archival reference image.", author: "Unknown", source: "British Museum", license: "CC BY-NC-SA 4.0", notes: "Side view.", img: "/assets/sanchi_archival.jpg" },
      { year: "2015", era: "Contemporary Reference", stamp: "SAN-M01", title: "Eastern Gateway / Torana", desc: "Curated contemporary reference image from the project dataset.", author: "Unknown", source: "TripInvites", license: "License needs confirmation", notes: "Front view; shown as source material, not a validated registration.", img: "/assets/sanchi_modern.jpg" },
      { year: "2017", era: "Contemporary Reference", stamp: "SAN-M02", title: "Sanchi Stupa, Side View", desc: "Curated contemporary reference image from the project dataset.", author: "Anandajoti Bhikkhu", source: "Wikimedia Commons", license: "Public Domain", notes: "Side view.", img: "/assets/sanchi_modern.jpg" }
    ], evidence: [], matches: []
  });

  Object.assign(monumentsData.qutb, {
    epochs: "1858–2017", statusText: "REGISTRATION OUTPUT AWAITING VERIFICATION", statusType: "warning",
    metrics: { predictedPoints: "—", ransacInliers: "—", inlierRatio: "Not available", reprojRmse: "Not available", facadeAlign: "Not verified", parallaxGap: "Not verified", hMatrix: [["—", "—", "—"], ["—", "—", "—"], ["—", "—", "—"]], hCond: "Not available", hDet: "Not available", hSupport: "Not available", vSupport: "Not available", hullCoverage: "Not available", confMean: "Not available" },
    timeline: [
      { year: "1858", era: "Archival Reference", stamp: "QUT-H01", title: "Qutb Minar, Full-height View", desc: "Curated archival reference image from the project dataset.", author: "Unknown", source: "Wikimedia Commons", license: "CC0 1.0", notes: "Full-height vertical view.", img: "/assets/qutb_archival.jpg" },
      { year: "1860", era: "Archival Reference", stamp: "QUT-H02", title: "Qutb Minar, Decorative Detail", desc: "Curated archival reference image from the project dataset.", author: "Samuel Bourne", source: "Wikimedia Commons", license: "Public Domain", notes: "Closer decorative-elements view.", img: "/assets/qutb_archival.jpg" },
      { year: "2008", era: "Contemporary Reference", stamp: "QUT-M01", title: "Qutb Minar Tower", desc: "Curated contemporary reference image from the project dataset.", author: "Ondřej Žváček", source: "Wikipedia", license: "GFDL / CC BY-SA", notes: "Vertical/full view.", img: "/assets/qutb_modern.jpg" },
      { year: "2017", era: "Contemporary Reference", stamp: "QUT-M04", title: "Qutb Minar, Full View", desc: "Curated contemporary reference image from the project dataset.", author: "Pragyanand Raushan", source: "Wikimedia Commons", license: "CC BY-SA 4.0", notes: "South-side full view.", img: "/assets/qutb_modern.jpg" }
    ], evidence: [], matches: []
  });

  return monumentsData;
}

export function formatMatrix(matrix) {
  return matrix.map(row => row.map(value => Number(value).toPrecision(5)));
}

export function evidenceForUi(candidate, index) {
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
