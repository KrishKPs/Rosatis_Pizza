import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { Meta } from "../api/types";

interface FiltersState {
  meta: Meta | null;
  start: string;
  end: string;
  channel: string; // "" = all channels
  setStart: (s: string) => void;
  setEnd: (s: string) => void;
  setChannel: (c: string) => void;
  resetRange: () => void;
  refreshKey: number;
  bumpRefresh: () => void;
}

const FiltersContext = createContext<FiltersState | null>(null);

export function FiltersProvider({ children }: { children: ReactNode }) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [channel, setChannel] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    api.meta().then((m) => {
      setMeta(m);
      setStart(m.date_min);
      setEnd(m.date_max);
    });
  }, []);

  const resetRange = () => {
    if (meta) {
      setStart(meta.date_min);
      setEnd(meta.date_max);
    }
    setChannel("");
  };

  const value = useMemo(
    () => ({
      meta,
      start,
      end,
      channel,
      setStart,
      setEnd,
      setChannel,
      resetRange,
      refreshKey,
      bumpRefresh: () => setRefreshKey((k) => k + 1),
    }),
    [meta, start, end, channel, refreshKey],
  );

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters(): FiltersState {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error("useFilters must be used within FiltersProvider");
  return ctx;
}
