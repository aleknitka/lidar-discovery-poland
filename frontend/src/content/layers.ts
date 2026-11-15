// Plain-language explanations of every layer ("product kind") the backend can produce, plus the
// general background shown in the Info tab. Typed data, one entry per kind.
//
// To add a kind: (1) add it to ALL_KINDS in src/lidar_discovery/processing/pipeline.py,
// (2) add an entry to LAYER_INFO below (the layers.test.ts completeness test enforces this),
// (3) add it to LAYER_CHOICES if users may pick it when fetching data.
//
// The numbers quoted here are the ProcessParams defaults in processing/pipeline.py and the
// algorithms in processing/vis.py and processing/dtm.py. They are fixed in the backend: the web
// app has no controls for them. Keep this file in step with those files.

export type KnownKind = 'dtm' | 'hillshade' | 'slope' | 'svf' | 'lrm' | 'ground_density';

/** Display order everywhere (matches ALL_KINDS in the backend). */
export const KIND_ORDER: KnownKind[] = [
  'dtm',
  'hillshade',
  'slope',
  'svf',
  'lrm',
  'ground_density',
];

export type Suitability = 'best' | 'good' | 'weak';

export interface FeatureNote {
  /** Plain feature name, e.g. "House platforms". */
  feature: string;
  suitability: Suitability;
  note: string;
}

export interface LayerInfo {
  kind: KnownKind;
  /** Human-readable name shown in lists. */
  name: string;
  /** Short name used in tight spaces (checkbox labels, map titles). */
  shortName: string;
  /** Technical name, shown small next to the human name. */
  technical: string;
  /** One line shown under the layer in the Layers list. */
  hint: string;
  /** What it is, in one sentence. */
  what: string;
  /** How it is computed here: the actual parameters. */
  computed: string[];
  /** How to read it. */
  read: { bright: string; dark: string; ramp: string };
  /** What to look for in this project. */
  lookFor: FeatureNote[];
  /** Common false positives and pitfalls. */
  pitfalls: string[];
  /** Which parameters matter, and the current state of tuning. */
  tuning: string[];
}

const TUNING_FIXED =
  'All processing parameters are fixed in the backend (ProcessParams in processing/pipeline.py). The web app has no controls for them. Changing one means editing that file and rebuilding the area.';

export const LAYER_INFO: Record<KnownKind, LayerInfo> = {
  dtm: {
    kind: 'dtm',
    name: 'Bare-earth height (DTM)',
    shortName: 'Bare-earth height',
    technical: 'dtm',
    hint: 'Ground height with trees and buildings removed.',
    what: 'A digital terrain model (DTM): the height of the bare ground, with trees, shrubs and buildings taken out.',
    computed: [
      'Only points the data provider classified as ground (class 2) are used. Vegetation and building points are ignored.',
      'The ground points are joined into a triangle network (Delaunay TIN) and the height is interpolated linearly inside each triangle.',
      'Result: a 0.5 m grid in EPSG:2180 (the Polish national grid). Cells farther than 6 m from any ground point are left empty (transparent) instead of guessed.',
      'Stored as a Cloud-Optimised GeoTIFF with heights in metres.',
    ],
    read: {
      bright: 'Higher ground.',
      dark: 'Lower ground.',
      ramp: 'Blue-green (low) through sand and brown to white (high). The colours are stretched between the 1st and 99th percentile of the heights in this area, so they say "higher or lower than the rest of this area", not absolute height. Use the legend values, not the colour, for numbers.',
    },
    lookFor: [
      {
        feature: 'Terraces and large platforms',
        suitability: 'good',
        note: 'Visible as steps in the colour on slopes, but small features are hidden by the large height range. Use it for orientation, then switch to a relief layer.',
      },
      {
        feature: 'Everything small (cellar pits, house platforms)',
        suitability: 'weak',
        note: 'A pit 1 m deep on a hillside that drops 100 m is invisible in raw heights. This is why the other layers exist.',
      },
    ],
    pitfalls: [
      'Triangles are long where ground points are sparse (dense forest, water). The surface there is a straight line between distant points and can hide or invent features. Check the ground-point density layer.',
      'It is a model of the ground as the data provider classified it. Misclassified points (low vegetation labelled ground, or ground labelled vegetation) leave bumps and holes.',
      'Epochs use different vertical datums (KRON86 vs EVRF2007). Do not subtract one epoch from another.',
    ],
    tuning: [
      'Matters: grid size (0.5 m) and the 6 m gap limit. A coarser grid smooths small features away; a larger gap limit fills more holes with less trustworthy values.',
      TUNING_FIXED,
    ],
  },

  hillshade: {
    kind: 'hillshade',
    name: 'Shaded relief',
    shortName: 'Shaded relief',
    technical: 'hillshade',
    hint: 'The terrain lit from 16 directions at once.',
    what: 'A picture of the ground as if lit by the sun, so bumps and hollows show as light and shadow.',
    computed: [
      'Computed from the 0.5 m DTM. The slope and facing direction of each cell are compared with a light source.',
      'The light is placed at 16 equally spaced compass directions, 35 degrees above the horizon, and the 16 results are averaged. Averaging removes the classic problem that features lined up with a single light direction vanish.',
      'No vertical exaggeration (1x). Values run from 0 to 1.',
    ],
    read: {
      bright: 'Surfaces facing the light or flat ground.',
      dark: 'Steep surfaces and deep hollows.',
      ramp: 'Plain greyscale, 0 (black) to 1 (white). Flat ground is a mid-light grey.',
    },
    lookFor: [
      {
        feature: 'Terraces',
        suitability: 'best',
        note: 'Step-like bands on a slope appear as parallel light/dark stripes.',
      },
      {
        feature: 'Holloways (sunken roads)',
        suitability: 'best',
        note: 'Long, narrow, dark-edged grooves running down or across a slope.',
      },
      {
        feature: 'House platforms',
        suitability: 'good',
        note: 'Flat rectangles cut into a slope: a lit flat with a dark back edge. Local relief usually shows them more clearly.',
      },
      {
        feature: 'Field boundaries',
        suitability: 'good',
        note: 'Low banks and lynchets show as thin lines.',
      },
    ],
    pitfalls: [
      'Shading is easy to over-trust: it looks like a photograph, but it is a calculation. Always look at a second layer before believing a feature.',
      'Noise in the DTM (from sparse ground points) becomes visible texture. Speckle that does not follow any logic is usually noise.',
      'Because the 16 directions are averaged, contrast is lower than a single-direction hillshade. That is deliberate.',
    ],
    tuning: [
      'Matters: sun elevation (35 degrees; lower reveals subtle features but throws long shadows), number of directions (16), vertical exaggeration (1x).',
      TUNING_FIXED,
    ],
  },

  slope: {
    kind: 'slope',
    name: 'Slope',
    shortName: 'Slope',
    technical: 'slope',
    hint: 'Steepness in degrees; flat ground is bright.',
    what: 'How steep the ground is at each point, in degrees.',
    computed: [
      'Computed from the 0.5 m DTM using the height difference between neighbouring cells (central differences).',
      'Output in degrees, 0 (flat) to 90 (vertical).',
      'Displayed between 0 and 45 degrees; anything steeper is drawn as the darkest value.',
    ],
    read: {
      bright: 'Flat or gently sloping ground.',
      dark: 'Steep ground.',
      ramp: 'Greyscale, inverted on purpose: 0 degrees is white, 45 degrees or more is black.',
    },
    lookFor: [
      {
        feature: 'Terraces and house platforms',
        suitability: 'best',
        note: 'Man-made flats are unnaturally flat. They appear as bright patches or bands on otherwise dark slopes, with a dark line at the retaining edge.',
      },
      {
        feature: 'Holloways',
        suitability: 'good',
        note: 'Dark banks on both sides of a bright, flat road bed.',
      },
      {
        feature: 'Cellar pits',
        suitability: 'good',
        note: 'A dark ring (the pit walls) around a bright floor.',
      },
    ],
    pitfalls: [
      'Slope has no direction, so it cannot tell a pit from a mound. Pair it with Sky-view factor or Local relief.',
      'Very sensitive to noise: small errors in height turn into spurious steepness on flat ground.',
    ],
    tuning: [
      'Matters: grid size (0.5 m; finer grids are noisier) and the display range (0-45 degrees).',
      TUNING_FIXED,
    ],
  },

  svf: {
    kind: 'svf',
    name: 'Sky-view factor',
    shortName: 'Sky-view factor',
    technical: 'svf',
    hint: 'How much sky a spot sees; pits and hollows go dark.',
    what: 'The fraction of the sky you would see from each spot on the ground: close to 1 on open ground, lower in pits, hollows and sunken roads.',
    computed: [
      'For every cell, look outward in 16 directions up to a 10 m radius on the 0.5 m DTM and find the highest horizon in each direction.',
      'SVF = 1 minus the average of the sine of those horizon angles (angles below the horizontal count as zero).',
      'Cells are sampled at whole-cell offsets with denser sampling near the cell. Computed in strips so large areas fit in memory.',
      'Displayed between 0.7 and 1.0.',
    ],
    read: {
      bright: 'Open ground: flat areas, ridges, mounds (a lot of sky visible).',
      dark: 'Enclosed ground: pits, hollows, sunken roads, the foot of a bank.',
      ramp: 'Greyscale from 0.7 (black) to 1.0 (white). Most flat ground is near white, so the interesting detail is in the dark end.',
    },
    lookFor: [
      {
        feature: 'Cellar pits',
        suitability: 'best',
        note: 'Small, dark, roughly rectangular or round spots, 2 to 6 m across.',
      },
      {
        feature: 'Holloways (sunken roads)',
        suitability: 'best',
        note: 'Continuous dark lines. Because the result does not depend on a light direction, roads at any orientation show equally well.',
      },
      {
        feature: 'House platforms',
        suitability: 'good',
        note: 'Often visible as a bright flat with a dark edge where it is cut into the slope.',
      },
      {
        feature: 'Field boundaries and ditches',
        suitability: 'good',
        note: 'Ditches show as dark lines, low banks as faint bright lines.',
      },
    ],
    pitfalls: [
      'Natural pits look identical to cellars: windthrow pits (from fallen trees), sinkholes and old tree-stump holes are the main look-alikes in the Bieszczady forests.',
      'Charcoal-burning platforms are round flat shelves that can be mistaken for house platforms.',
      'Artefacts: a straight-edged dark patch or a grid pattern often comes from the interpolation or from where the sheet boundary lies, not from the ground. Check ground-point density.',
      'The 10 m radius means features larger than about 20 m across (big hollows, valleys) are not emphasised.',
    ],
    tuning: [
      'Matters most: search radius (10 m; larger shows broader hollows, smaller shows only the tightest pits) and number of directions (16). Display range (0.7-1.0) changes contrast only.',
      TUNING_FIXED,
    ],
  },

  lrm: {
    kind: 'lrm',
    name: 'Local relief',
    shortName: 'Local relief',
    technical: 'lrm',
    hint: 'Small bumps and dips with the big hills removed.',
    what: 'The ground with the broad hills and valleys subtracted, so only small bumps and dips remain: a local relief model (LRM).',
    computed: [
      'LRM = DTM minus a smoothed copy of itself. The smoothing is a Gaussian blur with a sigma of 10 m (about 20 m wavelengths and longer are removed), computed so that empty cells do not drag the average down.',
      'Output in metres above or below the local average. Displayed between -1 m and +1 m.',
    ],
    read: {
      bright: 'Higher than the surroundings: banks, mounds, platform edges, wall lines.',
      dark: 'Lower than the surroundings: pits, ditches, road beds.',
      ramp: 'Greyscale: -1 m or lower is black, 0 m (no local relief) is mid-grey, +1 m or higher is white. The scale is in real metres, so a 30 cm bank is a gentle grey step.',
    },
    lookFor: [
      {
        feature: 'House platforms',
        suitability: 'best',
        note: 'A flat, slightly raised rectangle (or a bench cut into the slope) about 5 to 10 m across.',
      },
      {
        feature: 'Field boundaries',
        suitability: 'best',
        note: 'Long straight low banks or ditches, often meeting at right angles.',
      },
      {
        feature: 'Cellar pits',
        suitability: 'good',
        note: 'A dark hollow, sometimes with a bright rim of spoil. The depth is readable in metres.',
      },
      {
        feature: 'Cemeteries and church sites',
        suitability: 'good',
        note: 'Rows of low mounds or a rectangular platform with a surrounding bank. Interpret with extra care and keep the location restricted.',
      },
      {
        feature: 'Holloways',
        suitability: 'good',
        note: 'Dark channels with bright banks.',
      },
    ],
    pitfalls: [
      'At the edge of a steep slope the blur mixes uphill and downhill heights, producing a bright or dark halo that is not a feature.',
      'Windthrow pits and mounds, charcoal hearths and old skid trails all look like small relief. Look for regular shapes and alignments, not single blobs.',
      'Within roughly 30 m of the edge of a fetched area the result is less reliable. If it was added later from an existing DTM, the area edge is padded by copying the border heights.',
    ],
    tuning: [
      'Matters most: filter size (sigma 10 m). A smaller sigma keeps only the finest detail; a larger one lets bigger landforms through. Display range (+/-1 m) changes contrast only.',
      TUNING_FIXED,
    ],
  },

  ground_density: {
    kind: 'ground_density',
    name: 'Ground-point density',
    shortName: 'Ground-point density',
    technical: 'ground_density',
    hint: 'How many ground points back the surface; dark = trust less.',
    what: 'The number of laser points that reached the ground per square metre. It tells you how well the terrain is measured, not what the terrain looks like.',
    computed: [
      'Count the ground-classified (class 2) points in each 0.5 m cell, convert to points per m2, then average over a 4 m x 4 m window.',
      'Displayed between 0 and 8 points per m2.',
    ],
    read: {
      bright: 'Many ground points: the surface is well measured.',
      dark: 'Few or no ground points: the surface was interpolated over a gap.',
      ramp: 'Greyscale from 0 (black) to 8 points per m2 (white).',
    },
    lookFor: [
      {
        feature: 'Trust check for every candidate',
        suitability: 'best',
        note: 'Before believing any feature in another layer, check the density at that spot. A pit 3 m across needs several points on its floor and rim to be real; with under about 1 point per m2 it may be an artefact.',
      },
      {
        feature: 'Canopy shadows and gaps',
        suitability: 'good',
        note: 'Dense conifer stands and wet ground return few ground points. Features there deserve more suspicion.',
      },
    ],
    pitfalls: [
      'High density does not guarantee a correct surface, and low density does not prove there is nothing there. It only tells you how much evidence the surface rests on.',
      'The counts depend on the ground classification by the data provider, and on the season: leaf-on flights (summer, autumn) have fewer ground returns under broadleaf trees than leaf-off (spring).',
    ],
    tuning: [
      'Matters: window size (4 m; smaller is noisier, larger blurs small gaps) and the display range (0-8 points per m2).',
      TUNING_FIXED,
    ],
  },
};

/** Fallback for a kind the backend added but this file does not describe yet. */
export function layerInfo(kind: string): LayerInfo | null {
  return (LAYER_INFO as Record<string, LayerInfo | undefined>)[kind] ?? null;
}

export function displayName(kind: string): string {
  return layerInfo(kind)?.name ?? kind;
}

export function shortName(kind: string): string {
  return layerInfo(kind)?.shortName ?? kind;
}

export function layerHint(kind: string): string {
  return layerInfo(kind)?.hint ?? '';
}

/** Sort rank for a kind (unknown kinds last). */
export function kindRank(kind: string): number {
  const i = KIND_ORDER.indexOf(kind as KnownKind);
  return i < 0 ? KIND_ORDER.length : i;
}

/** The layers a user can pick when fetching data. */
export interface LayerChoice {
  kind: KnownKind;
  /** Always built (checkbox shown checked and disabled). */
  required?: boolean;
  /** Ticked by default. */
  defaultOn: boolean;
  /** Note shown next to the checkbox. */
  note?: string;
}

export const LAYER_CHOICES: LayerChoice[] = [
  { kind: 'dtm', required: true, defaultOn: true, note: 'required by all others' },
  { kind: 'hillshade', defaultOn: true },
  { kind: 'slope', defaultOn: true },
  { kind: 'svf', defaultOn: true },
  { kind: 'lrm', defaultOn: true },
  { kind: 'ground_density', defaultOn: true },
];

export const DEFAULT_LAYERS: KnownKind[] = LAYER_CHOICES.filter((c) => c.defaultOn).map(
  (c) => c.kind,
);

/** Canonical comma-separated `layers` parameter: DTM always included, canonical order. */
export function layersParam(selected: Iterable<string>): string {
  const set = new Set(selected);
  set.add('dtm');
  return [...set].sort((a, b) => kindRank(a) - kindRank(b)).join(',');
}

/** Which layer to look at for which feature (one line each, for the Info tab). */
export const FEATURE_GUIDE: { feature: string; layers: KnownKind[]; why: string }[] = [
  {
    feature: 'House platforms',
    layers: ['lrm', 'hillshade', 'slope'],
    why: 'Flat benches and low rectangles: local relief shows height, slope shows flatness.',
  },
  {
    feature: 'Cellar pits',
    layers: ['svf', 'lrm'],
    why: 'Small enclosed hollows: sky-view factor makes them dark, local relief gives depth.',
  },
  {
    feature: 'Terraces',
    layers: ['hillshade', 'slope'],
    why: 'Parallel steps on a slope read best as light and shadow or as bright flats.',
  },
  {
    feature: 'Holloways (sunken roads)',
    layers: ['svf', 'hillshade'],
    why: 'Long continuous grooves: sky-view factor is independent of the light direction.',
  },
  {
    feature: 'Field boundaries',
    layers: ['lrm', 'slope'],
    why: 'Low banks and ditches only a few tens of centimetres high.',
  },
  {
    feature: 'Cemetery and church sites',
    layers: ['lrm', 'svf'],
    why: 'Platforms with banks and rows of low mounds. Keep these restricted.',
  },
  {
    feature: 'Is the surface trustworthy here?',
    layers: ['ground_density'],
    why: 'Check this for every candidate before believing it.',
  },
];

// ------------------------------------------------------------------------- general background
export interface InfoSection {
  title: string;
  paragraphs: string[];
}

export const LIDAR_PRIMER: InfoSection = {
  title: 'How LiDAR sees through trees',
  paragraphs: [
    'An aircraft fires hundreds of thousands of laser pulses per second at the ground. A pulse that hits a tree can produce several echoes ("returns"): the first from the top of the canopy, later ones from branches, and sometimes a last one from the ground, where a gap in the leaves lets some light through. The last returns are the ones that map the ground.',
    'After the flight, the provider sorts every point into classes: ground, low/medium/high vegetation, buildings, noise. This project uses only the ground class (class 2). That is "seeing through the trees": the trees are not removed from the picture, the points that bounced off them are simply left out.',
    'Point density matters. At about 4 points per m2 (the 2012 flights) only a fraction reach the ground under dense forest, so the ground surface can be built from one point every few metres in places. A cellar pit 3 m across may then be covered by one or two points. The Ground-point density layer shows exactly where the surface is well measured and where it is mostly interpolation. Use it to decide how far to trust a feature.',
    'Season matters too. Leaves block the laser: spring flights (before leaf-out) usually give more ground returns under broadleaf trees than summer or autumn flights. Conifers block it all year.',
    'A candidate feature is a pattern in a calculated surface, not an observation. It needs the same shape in more than one layer, a plausible position (a platform near a stream or a road, a pit in a line with others), good local point density, and a check against historical maps and known sites before it is called anything but a candidate.',
  ],
};

export interface GlossaryEntry {
  term: string;
  definition: string;
}

export const GLOSSARY: GlossaryEntry[] = [
  {
    term: 'DTM (digital terrain model)',
    definition:
      'The height of the bare ground. Trees and buildings are removed. This is what this project analyses.',
  },
  {
    term: 'DSM (digital surface model)',
    definition:
      'The height of the top of everything: tree canopy, roofs and ground. Not built here; the difference DSM minus DTM would be the height of vegetation and buildings.',
  },
  {
    term: 'Hillshade',
    definition:
      'A grey picture of the terrain lit by an imaginary sun. Here, the average of 16 sun directions at 35 degrees elevation.',
  },
  {
    term: 'Slope',
    definition: 'Steepness of the ground in degrees. 0 is flat, 90 is a vertical wall.',
  },
  {
    term: 'SVF (sky-view factor)',
    definition:
      'The fraction of the sky visible from a point. 1 is fully open, lower values mean the point sits in a pit or hollow. Here: 16 directions, 10 m radius.',
  },
  {
    term: 'LRM (local relief model)',
    definition:
      'The DTM minus a blurred copy of itself, which leaves only small-scale bumps and dips. Here the blur has a sigma of 10 m.',
  },
  {
    term: 'Point density',
    definition:
      'Laser points per square metre. Total density counts every return; ground density counts only the points classified as ground and is what limits the detail of the DTM.',
  },
  {
    term: 'Ground classification',
    definition:
      'Sorting laser points into classes (ground = 2, vegetation, buildings...). Done by the data provider with software; it has errors.',
  },
  {
    term: 'Epoch',
    definition:
      'A survey year. The same place may be flown more than once (here: 2012 and 2023). Epochs differ in density, season and vertical datum, so compare them by eye, never by subtraction.',
  },
  {
    term: 'Vertical datum (KRON86, EVRF2007)',
    definition:
      'The zero level that heights are measured from. The older flights use KRON86, the newer EVRF2007; they are not aligned in this project.',
  },
  {
    term: 'EPSG:2180',
    definition:
      'The Polish national map projection (PUWG 1992). Grids and map-sheet outlines are in it; the web map shows the results reprojected to Web Mercator.',
  },
  {
    term: 'Map sheet',
    definition:
      'GUGiK publishes LiDAR as tiles of about 1.2 km x 1.2 km, each a LAZ file of roughly 100 to 600 MB. A download always fetches whole sheets, however small your view is.',
  },
  {
    term: 'LAZ',
    definition: 'A compressed point-cloud file format (LAS compressed with LASzip).',
  },
  {
    term: 'COG (Cloud-Optimised GeoTIFF)',
    definition:
      'The raster format used for the derived layers, built so the map can read small pieces quickly.',
  },
  {
    term: 'Windthrow pit',
    definition:
      'The hole and mound left when a tree is blown over and its roots tear out. The commonest natural look-alike for a cellar pit in these forests.',
  },
  {
    term: 'Candidate',
    definition:
      'A feature that might be man-made, recorded with its evidence. It stays a candidate until it is checked against historical sources.',
  },
];

/** The "metadata of the layer" rows shown in the Info tab, from the API layer object. */
export function metadataRows(layer: {
  epoch: number;
  source_id: string;
  resolution_m?: number;
  provenance?: Record<string, unknown>;
}): { label: string; value: string }[] {
  const p = layer.provenance ?? {};
  const rows: { label: string; value: string }[] = [
    { label: 'Epoch', value: String(layer.epoch) },
    { label: 'Source', value: layer.source_id },
  ];
  if (layer.resolution_m != null)
    rows.push({ label: 'Resolution', value: `${layer.resolution_m} m` });
  const str = (k: string) => (typeof p[k] === 'string' ? (p[k] as string) : null);
  if (str('crs_xy')) rows.push({ label: 'Grid', value: str('crs_xy')! });
  if (str('crs_h')) rows.push({ label: 'Vertical datum', value: str('crs_h')! });
  const range = p.display_range;
  if (Array.isArray(range) && range.length === 2)
    rows.push({
      label: 'Colour range',
      value: `${Number(range[0]).toFixed(2)} to ${Number(range[1]).toFixed(2)}`,
    });
  if (typeof p.valid_fraction === 'number')
    rows.push({ label: 'Cells with data', value: `${Math.round(p.valid_fraction * 100)} %` });
  const stats = p.point_stats as { points_ground?: number; points_total?: number } | undefined;
  if (stats?.points_ground != null)
    rows.push({
      label: 'Ground points used',
      value: `${stats.points_ground.toLocaleString('en')}${
        stats.points_total ? ` of ${stats.points_total.toLocaleString('en')}` : ''
      }`,
    });
  if (str('computed_from')) rows.push({ label: 'Computed from', value: str('computed_from')! });
  const inputs = p.inputs;
  if (Array.isArray(inputs) && inputs.length)
    rows.push({ label: 'Input sheets', value: String(inputs.length) });
  if (str('created_at')) rows.push({ label: 'Created', value: str('created_at')! });
  if (str('code_version')) rows.push({ label: 'Code version', value: str('code_version')! });
  const params = p.parameters;
  if (params && typeof params === 'object')
    rows.push({
      label: 'Parameters',
      value: Object.entries(params as Record<string, unknown>)
        .map(([k, v]) => `${k}=${String(v)}`)
        .join(', '),
    });
  return rows;
}
