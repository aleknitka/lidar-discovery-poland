// How layers and the background map are drawn. Pure helpers so they can be unit tested.

/** auto = height in muted colours, every other layer grey; colour = blue (low) to red (high); bw = grey. */
export type ColourMode = 'default' | 'colour' | 'bw';
export const COLOUR_MODES: { value: ColourMode; label: string; title: string }[] = [
  { value: 'default', label: 'Auto', title: 'Height in soft colours, other layers in grey' },
  { value: 'colour', label: 'Colour', title: 'Every layer from blue (low) to red (high)' },
  { value: 'bw', label: 'B&W', title: 'Every layer in black (low) to white (high)' },
];
export const isColourMode = (v: unknown): v is ColourMode =>
  v === 'default' || v === 'colour' || v === 'bw';

/** Tile URL for a colour mode. Auto is the server default, so it adds nothing. */
export function styledTileUrl(url: string, mode: ColourMode): string {
  if (mode === 'default') return url;
  return `${url}${url.includes('?') ? '&' : '?'}style=${mode}`;
}

export type BasemapId = 'osm' | 'photo';
export const isBasemapId = (v: unknown): v is BasemapId => v === 'osm' || v === 'photo';

/** GUGiK orthophoto (aerial photo), a public WMTS in Web Mercator. */
export const PHOTO_TILES =
  'https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMTS/StandardResolution' +
  '?service=WMTS&request=GetTile&version=1.0.0&layer=ORTOFOTOMAPA&style=default' +
  '&format=image/jpeg&tilematrixset=EPSG:3857&tilematrix=EPSG:3857:{z}&tilerow={y}&tilecol={x}';
