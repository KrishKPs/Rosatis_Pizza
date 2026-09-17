import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { CountSheetItem, CountSheetResponse, CountStatus } from "../api/types";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { StatusPill } from "../components/ui/StatusPill";
import { dateTime } from "../lib/format";

const GROUPS: { kind: CountSheetItem["kind"]; label: string; hint: string }[] = [
  { kind: "packaging", label: "Boxes & packaging", hint: "Count the flattened stack for each size." },
  { kind: "food", label: "Food & ingredients", hint: "Compare to what the register thinks you have left." },
  { kind: "supply", label: "Supplies", hint: "Napkins, bags, gloves — never tracked by an order, count these by hand." },
];

function liveStatus(typed: string, reorderPoint: number): CountStatus | null {
  if (typed.trim() === "") return null;
  const n = Number(typed);
  if (Number.isNaN(n)) return null;
  if (n <= 0) return "out";
  if (n <= reorderPoint) return "low";
  return "ok";
}

export function InventoryCountPanel() {
  const [sheet, setSheet] = useState<CountSheetResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [countedBy, setCountedBy] = useState("");
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [copyMsg, setCopyMsg] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api.countSheet().then((s) => {
      setSheet(s);
      setLoading(false);
    });
  };

  useEffect(load, []);

  const itemsByKind = useMemo(() => {
    const map: Record<string, CountSheetItem[]> = { packaging: [], food: [], supply: [] };
    for (const i of sheet?.items ?? []) map[i.kind]?.push(i);
    return map;
  }, [sheet]);

  const touchedCount = Object.values(inputs).filter((v) => v.trim() !== "").length;

  const save = async () => {
    if (!countedBy.trim() || touchedCount === 0) return;
    setSaving(true);
    const entries = Object.entries(inputs)
      .filter(([, v]) => v.trim() !== "" && !Number.isNaN(Number(v)))
      .map(([ingredient_id, v]) => ({ ingredient_id, counted_qty: Number(v) }));
    const res = await api.submitCount({ counted_by: countedBy.trim(), entries });
    setSheet(res);
    setInputs({});
    setSaving(false);
    setSavedMsg(`Saved — ${entries.length} item${entries.length === 1 ? "" : "s"} counted.`);
    setTimeout(() => setSavedMsg(null), 4000);
  };

  const copyReorderList = async () => {
    if (!sheet) return;
    const lines = sheet.reorder_list.map(
      (r) => `${r.name}: order ${r.suggested_order_qty ?? "?"} ${r.unit} (on hand ${r.on_hand ?? "?"} ${r.unit})`,
    );
    const text = lines.length ? lines.join("\n") : "Nothing to reorder right now.";
    try {
      await navigator.clipboard.writeText(text);
      setCopyMsg("Copied to clipboard.");
    } catch {
      setCopyMsg("Couldn't access clipboard — select and copy the list below.");
    }
    setTimeout(() => setCopyMsg(null), 3000);
  };

  if (loading || !sheet) {
    return <div className="py-24 text-center font-mono text-text-tertiary">Loading…</div>;
  }

  return (
    <div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Items to reorder"
          value={sheet.kpis.items_to_reorder.toString()}
          tone={sheet.kpis.items_to_reorder > 0 ? "loss" : "profit"}
        />
        <StatCard label="Completely out" value={sheet.kpis.items_out.toString()} tone={sheet.kpis.items_out > 0 ? "loss" : "neutral"} />
        <StatCard label="Never counted yet" value={sheet.kpis.items_never_counted.toString()} tone="neutral" />
      </div>

      <div className="mt-3 text-[12.5px] text-text-tertiary">
        {sheet.kpis.last_session_at ? (
          <>Last full count {dateTime(sheet.kpis.last_session_at)} by {sheet.kpis.last_session_by}.</>
        ) : (
          <>No manual count has been saved yet — the numbers below are the register's best guess. Walk the store and enter real counts below.</>
        )}
      </div>

      {sheet.reorder_list.length > 0 && (
        <Card
          className="mt-4"
          title="What to order next"
          subtitle="Everything at or under its reorder point, based on the latest count."
          action={
            <button
              onClick={copyReorderList}
              className="rounded-lg border border-border bg-surface-2 px-3 py-1.5 font-mono text-[12px] text-text-secondary hover:text-accent"
            >
              Copy list for supplier
            </button>
          }
        >
          {copyMsg && <div className="mb-2 text-[12px] text-accent">{copyMsg}</div>}
          <div className="flex flex-col gap-1.5">
            {sheet.reorder_list.map((r) => (
              <div key={r.ingredient_id} className="flex items-center justify-between rounded-lg px-3 py-2" style={{
                background: r.status === "out" ? "var(--loss-bg)" : "var(--accent-bg)",
              }}>
                <span className="text-[13px] text-text-primary">{r.name}</span>
                <span className="font-mono text-[12px] text-text-secondary">
                  on hand {r.on_hand ?? "—"} {r.unit} · order {r.suggested_order_qty ?? "—"} {r.unit}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card
        className="mt-4"
        title="Manual count sheet"
        subtitle="Walk the store, count what's actually there, and type it in below — same check as the clipboard, just digital."
        action={
          <div className="flex items-center gap-2">
            <input
              value={countedBy}
              onChange={(e) => setCountedBy(e.target.value)}
              placeholder="Counted by…"
              className="w-32 rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 font-mono text-[12.5px] text-text-primary outline-none placeholder:text-text-tertiary focus:border-accent/50"
            />
            <button
              onClick={save}
              disabled={saving || !countedBy.trim() || touchedCount === 0}
              className="rounded-lg bg-accent px-3 py-1.5 font-mono text-[12px] font-medium text-surface-1 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {saving ? "Saving…" : `Save count${touchedCount ? ` (${touchedCount})` : ""}`}
            </button>
          </div>
        }
      >
        {savedMsg && (
          <div
            className="mb-3 rounded-lg px-3 py-2 text-[12.5px] text-profit"
            style={{ background: "var(--profit-bg)" }}
          >
            {savedMsg}
          </div>
        )}
        <div className="flex flex-col gap-5">
          {GROUPS.map((g) => (
            <div key={g.kind}>
              <div className="mb-1.5 flex items-baseline justify-between">
                <h4 className="font-mono text-[12px] font-medium text-text-secondary">{g.label}</h4>
                <span className="text-[11.5px] text-text-tertiary">{g.hint}</span>
              </div>
              <div className="overflow-x-auto"><table className="w-full min-w-[520px]">
                <thead>
                  <tr className="border-b border-border text-left font-mono text-[11px] text-text-tertiary">
                    <th className="pb-1.5 font-medium">Item</th>
                    <th className="pb-1.5 text-right font-medium">Register says</th>
                    <th className="pb-1.5 text-right font-medium">Last count</th>
                    <th className="pb-1.5 text-right font-medium">Today's count</th>
                    <th className="pb-1.5 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {itemsByKind[g.kind]?.map((i) => {
                    const typed = inputs[i.ingredient_id] ?? "";
                    const status = liveStatus(typed, i.reorder_point) ?? i.status;
                    return (
                      <tr key={i.ingredient_id} className="border-b border-border/60 last:border-0">
                        <td className="py-1.5 text-[13px] text-text-primary">{i.name}</td>
                        <td className="py-1.5 text-right font-mono text-[12px] text-text-tertiary">
                          {i.system_expected !== null ? `${i.system_expected} ${i.unit}` : "—"}
                        </td>
                        <td className="py-1.5 text-right font-mono text-[12px] text-text-secondary">
                          {i.last_count_qty !== null ? `${i.last_count_qty} ${i.unit}` : "never"}
                        </td>
                        <td className="py-1.5 text-right">
                          <input
                            value={typed}
                            onChange={(e) =>
                              setInputs((s) => ({ ...s, [i.ingredient_id]: e.target.value.replace(/[^0-9.]/g, "") }))
                            }
                            placeholder="—"
                            inputMode="decimal"
                            className="w-20 rounded border border-border bg-surface-2 px-1.5 py-0.5 text-right font-mono text-[12.5px] text-text-primary outline-none focus:border-accent/50"
                          />
                        </td>
                        <td className="py-1.5 text-right">
                          <StatusPill status={status} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table></div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
