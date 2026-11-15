import type { Disclosure } from '../api/types';

export interface DisclosureInfo {
  label: string;
  tone: 'ok' | 'warn' | 'danger';
  description: string;
  /** Hidden from the API when LDP_PUBLIC_MODE=true. */
  hiddenInPublicMode: boolean;
  /** Geometry is snapped to a 1 km grid cell centroid in public mode. */
  snappedInPublicMode: boolean;
}

export function disclosureInfo(d: Disclosure | undefined): DisclosureInfo {
  switch (d) {
    case 'public':
      return {
        label: 'Public',
        tone: 'ok',
        description: 'Exact geometry may be shown in the public catalogue.',
        hiddenInPublicMode: false,
        snappedInPublicMode: false,
      };
    case 'generalised':
      return {
        label: 'Generalised',
        tone: 'warn',
        description: 'Public catalogue shows a position snapped to a 1 km grid cell.',
        hiddenInPublicMode: false,
        snappedInPublicMode: true,
      };
    case 'restricted':
      return {
        label: 'Restricted',
        tone: 'danger',
        description: 'Hidden from the public catalogue (e.g. cemeteries and graves).',
        hiddenInPublicMode: true,
        snappedInPublicMode: false,
      };
    default:
      // Unknown or missing: fail safe, treat as restricted.
      return {
        label: 'Unknown',
        tone: 'danger',
        description: 'Disclosure not set; treated as restricted.',
        hiddenInPublicMode: true,
        snappedInPublicMode: false,
      };
  }
}

/** Default disclosure for a new candidate: cemeteries and graves are restricted. */
export function defaultDisclosure(morphClass: string): Disclosure {
  return morphClass === 'cemetery' ? 'restricted' : 'generalised';
}

/** Whether the public catalogue (public mode) would show an item. */
export function visibleInPublic(d: Disclosure | undefined): boolean {
  return !disclosureInfo(d).hiddenInPublicMode;
}
