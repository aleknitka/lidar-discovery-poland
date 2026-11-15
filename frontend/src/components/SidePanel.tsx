import { useEffect, useRef, type KeyboardEvent, type ReactNode } from 'react';

export type TabId = 'layers' | 'info' | 'candidates' | 'places' | 'data';

export const TABS: { id: TabId; label: string }[] = [
  { id: 'layers', label: 'Layers' },
  { id: 'info', label: 'Info' },
  { id: 'candidates', label: 'Candidates' },
  { id: 'places', label: 'Places' },
  { id: 'data', label: 'Data' },
];

export const isTabId = (v: unknown): v is TabId => TABS.some((t) => t.id === v);

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tab: TabId;
  onTabChange: (tab: TabId) => void;
  /** Small counters/flags shown on tabs, e.g. an active job on "Data". */
  badges?: Partial<Record<TabId, string>>;
  children: ReactNode;
}

/**
 * Right-hand panel with tabs. Collapsible (the map then fills the screen) and, on narrow screens,
 * a bottom sheet. The open/closed state lives in the parent so it can be persisted.
 */
export default function SidePanel({
  open,
  onOpenChange,
  tab,
  onTabChange,
  badges,
  children,
}: Props) {
  const tabRefs = useRef<Partial<Record<TabId, HTMLButtonElement | null>>>({});
  const panelRef = useRef<HTMLElement>(null);
  const wasOpen = useRef(open);

  // Move focus into the panel when it opens from the closed state via the toggle, and back to the
  // floating toggle when it closes, so keyboard users never lose their place.
  useEffect(() => {
    if (wasOpen.current !== open) {
      const target = open
        ? tabRefs.current[tab]
        : document.querySelector<HTMLButtonElement>('[data-panel-open-button]');
      target?.focus({ preventScroll: true });
      wasOpen.current = open;
    }
  }, [open, tab]);

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const i = TABS.findIndex((t) => t.id === tab);
    let next = -1;
    if (e.key === 'ArrowRight') next = (i + 1) % TABS.length;
    else if (e.key === 'ArrowLeft') next = (i - 1 + TABS.length) % TABS.length;
    else if (e.key === 'Home') next = 0;
    else if (e.key === 'End') next = TABS.length - 1;
    if (next < 0) return;
    e.preventDefault();
    onTabChange(TABS[next].id);
    tabRefs.current[TABS[next].id]?.focus();
  };

  return (
    <aside
      id="side-panel"
      ref={panelRef}
      className={`side-panel ${open ? 'open' : 'closed'}`}
      aria-label="Map controls"
      hidden={!open}
      onKeyDown={(e) => {
        if (e.key === 'Escape' && open && window.matchMedia('(max-width: 720px)').matches)
          onOpenChange(false);
      }}
    >
      <div className="panel-head">
        <div role="tablist" aria-label="Panel sections" className="tabs" onKeyDown={onKeyDown}>
          {TABS.map((t) => (
            <button
              key={t.id}
              ref={(el) => {
                tabRefs.current[t.id] = el;
              }}
              role="tab"
              id={`tab-${t.id}`}
              aria-selected={tab === t.id}
              aria-controls={`tabpanel-${t.id}`}
              tabIndex={tab === t.id ? 0 : -1}
              className={`tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => onTabChange(t.id)}
            >
              {t.label}
              {badges?.[t.id] && <span className="tab-badge">{badges[t.id]}</span>}
            </button>
          ))}
        </div>
        <button
          className="panel-toggle"
          onClick={() => onOpenChange(false)}
          aria-label="Hide panel"
          aria-expanded={open}
          aria-controls="side-panel"
          title="Hide panel"
        >
          <span aria-hidden="true">▸</span>
          <span className="toggle-text">Hide</span>
        </button>
      </div>
      <div
        role="tabpanel"
        id={`tabpanel-${tab}`}
        aria-labelledby={`tab-${tab}`}
        className="panel-body"
        tabIndex={-1}
      >
        {children}
      </div>
    </aside>
  );
}

/** Floating button on the map that re-opens a collapsed panel. */
export function PanelOpenButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      className="panel-open"
      data-panel-open-button
      onClick={onClick}
      aria-label="Show panel"
      aria-expanded={false}
      aria-controls="side-panel"
      title="Show panel"
    >
      <span aria-hidden="true">◂</span>
      <span className="toggle-text">Panel</span>
    </button>
  );
}
