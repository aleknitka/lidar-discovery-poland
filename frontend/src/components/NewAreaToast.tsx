import { useEffect, useRef, useState } from 'react';
import { useLocations } from '../api/hooks';

export default function NewAreaToast() {
  const { data } = useLocations();
  const prev = useRef<string[] | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    if (!data) return;
    const ids = data.features.filter((f) => f.properties.kind === 'area').map((f) => f.properties.id);
    if (prev.current === null) {
      prev.current = ids;
      return;
    }
    const fresh = ids.filter((id) => !prev.current!.includes(id));
    if (fresh.length) setMsg(`New area: ${fresh.join(', ')}`);
    prev.current = ids;
    if (fresh.length) {
      const t = setTimeout(() => setMsg(null), 8000);
      return () => clearTimeout(t);
    }
  }, [data]);
  if (!msg) return null;
  return (
    <div
      role="status"
      style={{
        position: 'fixed',
        right: 16,
        bottom: 16,
        background: '#1a1a1a',
        color: '#fff',
        padding: '8px 12px',
        borderRadius: 6,
        fontSize: 13,
        zIndex: 9999,
      }}
    >
      {msg}
    </div>
  );
}
