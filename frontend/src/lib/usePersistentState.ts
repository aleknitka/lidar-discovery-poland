import { useCallback, useState } from 'react';

/** Read a JSON value from localStorage; any failure (blocked storage, bad JSON) gives `fallback`. */
export function readStored<T>(key: string, fallback: T, valid?: (v: unknown) => v is T): T {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw == null) return fallback;
    const v: unknown = JSON.parse(raw);
    return valid ? (valid(v) ? v : fallback) : (v as T);
  } catch {
    return fallback;
  }
}

export function writeStored(key: string, value: unknown): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable (private window, quota): the state just does not persist */
  }
}

/** useState that remembers its value in localStorage. */
export function usePersistentState<T>(
  key: string,
  initial: T,
  valid?: (v: unknown) => v is T,
): [T, (v: T | ((prev: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => readStored(key, initial, valid));
  const set = useCallback(
    (next: T | ((prev: T) => T)) => {
      setValue((prev) => {
        const v = typeof next === 'function' ? (next as (p: T) => T)(prev) : next;
        writeStored(key, v);
        return v;
      });
    },
    [key],
  );
  return [value, set];
}
