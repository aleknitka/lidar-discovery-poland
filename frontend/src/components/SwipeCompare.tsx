import { useCallback, useEffect, useRef, useState } from 'react';
import type { Map as MlMap } from 'maplibre-gl';
import MapView, { type MapViewProps, type RasterSpec } from './MapView';

interface Props extends Omit<MapViewProps, 'rasters' | 'attribution' | 'interactive'> {
  left: RasterSpec[];
  right: RasterSpec[];
  leftLabel: string;
  rightLabel: string;
}

/**
 * Swipe compare: two synced MapLibre maps. The right-hand map is stacked on top and clipped with
 * clip-path; it ignores pointer input and follows the left (primary) map's camera.
 */
export default function SwipeCompare({
  left,
  right,
  leftLabel,
  rightLabel,
  onMapReady,
  ...shared
}: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const primary = useRef<MlMap | null>(null);
  const secondary = useRef<MlMap | null>(null);
  const [pos, setPos] = useState(50); // percent from the left

  const sync = useCallback(() => {
    const a = primary.current;
    const b = secondary.current;
    if (!a || !b) return;
    b.jumpTo({
      center: a.getCenter(),
      zoom: a.getZoom(),
      bearing: a.getBearing(),
      pitch: a.getPitch(),
    });
  }, []);

  const wire = useCallback(() => {
    const a = primary.current;
    if (!a || !secondary.current) return;
    a.on('move', sync);
    sync();
  }, [sync]);

  useEffect(() => () => void primary.current?.off('move', sync), [sync]);

  const setFromClientX = (clientX: number) => {
    const r = wrap.current?.getBoundingClientRect();
    if (!r) return;
    setPos(Math.max(0, Math.min(100, ((clientX - r.left) / r.width) * 100)));
  };

  return (
    <div className="swipe" ref={wrap}>
      <MapView
        {...shared}
        rasters={left}
        attribution
        onMapReady={(m) => {
          primary.current = m;
          onMapReady?.(m);
          wire();
        }}
      />
      <div className="swipe-overlay" style={{ clipPath: `inset(0 0 0 ${pos}%)` }}>
        <MapView
          {...shared}
          onClick={undefined}
          rasters={right}
          attribution={false}
          interactive={false}
          onMapReady={(m) => {
            secondary.current = m;
            wire();
          }}
        />
      </div>
      <span className="swipe-label swipe-label-left">{leftLabel}</span>
      <span className="swipe-label swipe-label-right">{rightLabel}</span>
      <div
        className="swipe-handle"
        style={{ left: `${pos}%` }}
        role="slider"
        aria-label="Swipe divider"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pos)}
        tabIndex={0}
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId);
          setFromClientX(e.clientX);
        }}
        onPointerMove={(e) => {
          if (e.currentTarget.hasPointerCapture(e.pointerId)) setFromClientX(e.clientX);
        }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') setPos((p) => Math.max(0, p - 2));
          if (e.key === 'ArrowRight') setPos((p) => Math.min(100, p + 2));
        }}
      >
        <span className="swipe-grip">⇔</span>
      </div>
    </div>
  );
}
