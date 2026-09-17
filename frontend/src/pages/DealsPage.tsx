import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import type { DealStats } from "../api/types";
import { useFilters } from "../context/FiltersContext";
import { TopBar } from "../components/layout/TopBar";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { ProfitPill } from "../components/ui/StatusPill";
import { money, pct } from "../lib/format";
import { theme } from "../lib/theme";

export function DealsPage() {
  const { start, end, channel, refreshKey } = useFilters();
  const [deals, setDeals] = useState<DealStats[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const f = { start, end, channel: channel || undefined };

  useEffect(() => {
    if (!start || !end) return;
    setLoading(true);
    api.deals(f).then((d) => {
      setDeals(d);
      setSelected((cur) => cur ?? d[0]?.deal_id ?? null);
      setLoading(false);
    });
  }, [start, end, channel, refreshKey]);

  const totalTrueProfit = deals.reduce((s, d) => s + d.true_profit, 0);
  const totalRedemptions = deals.reduce((s, d) => s + d.redemptions, 0);
  const best = deals[0];
  const worst = deals[deals.length - 1];
  const chartData = [...deals].sort((a, b) => a.true_profit - b.true_profit);

  return (
    <div>
      <TopBar title="Deal Profit Optimizer" subtitle="Which of your deals actually make money?" />
      <div className="px-4 py-4 md:px-8 md:py-6">
        {loading || deals.length === 0 ? (
          <div className="py-24 text-center font-mono text-text-tertiary">Loading…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
              <StatCard
                label="True profit across all deals"
                value={money(totalTrueProfit)}
                hero
                tone={totalTrueProfit >= 0 ? "profit" : "loss"}
              />
              <StatCard label="Deal redemptions" value={totalRedemptions.toLocaleString()} />
              <StatCard label="Best earner" value={best?.name ?? "–"} />
              <StatCard
                label="Worst earner"
                value={worst?.name ?? "–"}
                tone={worst && worst.true_profit < 0 ? "loss" : "neutral"}
              />
            </div>

            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-5">
              <Card
                title="Ranked by true profit"
                subtitle="After removing customers who'd have ordered anyway, plus add-ons pulled in"
                className="lg:col-span-2"
                emphasis
              >
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
                    <CartesianGrid stroke={theme.border} horizontal={false} />
                    <XAxis
                      type="number"
                      tickFormatter={(v) => money(v)}
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 10.5 }}
                      tickLine={false}
                      axisLine={{ stroke: theme.border }}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={110}
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: theme.surface2,
                        border: `1px solid ${theme.border}`,
                        borderRadius: 8,
                        fontFamily: "IBM Plex Mono",
                        fontSize: 12,
                      }}
                      formatter={(v) => [money(Number(v)), "True profit"]}
                    />
                    <Bar
                      dataKey="true_profit"
                      radius={[0, 4, 4, 0]}
                      onClick={(d: any) => setSelected(d.deal_id)}
                      cursor="pointer"
                      isAnimationActive={false}
                    >
                      {chartData.map((d) => (
                        <Cell
                          key={d.deal_id}
                          fill={d.true_profit >= 0 ? theme.profit : theme.loss}
                          opacity={d.deal_id === selected ? 1 : 0.55}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              {selected && (
                <DealDetail
                  key={selected}
                  dealId={selected}
                  filters={f}
                  onSaved={() => api.deals(f).then(setDeals)}
                />
              )}
            </div>

            <div className="mt-4">
              <Card title="Head-to-head comparison" subtitle="All six deals, same math">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[900px]">
                    <thead>
                      <tr className="border-b border-border text-left font-mono text-[11px] text-text-tertiary">
                        <th className="pb-2 font-medium">Deal</th>
                        <th className="pb-2 text-right font-medium">Redemptions</th>
                        <th className="pb-2 text-right font-medium">Discount given</th>
                        <th className="pb-2 text-right font-medium">Cost to make</th>
                        <th className="pb-2 text-right font-medium">Add-ons pulled</th>
                        <th className="pb-2 text-right font-medium">Actual profit</th>
                        <th className="pb-2 text-right font-medium">True profit</th>
                        <th className="pb-2 text-right font-medium">Verdict</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deals.map((d) => (
                        <tr
                          key={d.deal_id}
                          onClick={() => setSelected(d.deal_id)}
                          className={`cursor-pointer border-b border-border/60 last:border-0 hover:bg-surface-2 ${
                            d.deal_id === selected ? "bg-surface-2" : ""
                          }`}
                        >
                          <td className="py-2.5">
                            <div className="text-[13px] text-text-primary">{d.name}</div>
                            <div className="font-mono text-[11px] text-text-tertiary">{d.code}</div>
                          </td>
                          <td className="py-2.5 text-right font-mono text-[12.5px] text-text-secondary">
                            {d.redemptions}
                          </td>
                          <td className="py-2.5 text-right font-mono text-[12.5px] text-text-secondary">
                            {money(d.discount_given)}
                          </td>
                          <td className="py-2.5 text-right font-mono text-[12.5px] text-text-secondary">
                            {money(d.food_cost)}
                          </td>
                          <td className="py-2.5 text-right font-mono text-[12.5px] text-text-secondary">
                            {money(d.attach_revenue)}
                          </td>
                          <td className="py-2.5 text-right font-mono text-[12.5px] text-text-primary">
                            {money(d.actual_profit)}
                          </td>
                          <td
                            className="py-2.5 text-right font-mono text-[13px] font-medium"
                            style={{ color: d.true_profit >= 0 ? "var(--profit)" : "var(--loss)" }}
                          >
                            {money(d.true_profit)}
                          </td>
                          <td className="py-2.5 text-right">
                            <ProfitPill value={d.true_profit} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function DealDetail({
  dealId,
  filters,
  onSaved,
}: {
  dealId: string;
  filters: { start: string; end: string; channel?: string };
  onSaved: () => void;
}) {
  const [saved, setSaved] = useState<DealStats | null>(null);
  const [incFrac, setIncFrac] = useState(0.5);
  const [attachEff, setAttachEff] = useState(0.5);
  const [preview, setPreview] = useState<DealStats | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.deal(dealId, filters).then((d) => {
      setSaved(d);
      setIncFrac(d.incremental_fraction);
      setAttachEff(d.attach_effect);
      setPreview(d);
    });
  }, [dealId]);

  useEffect(() => {
    if (!saved) return;
    const t = setTimeout(() => {
      api.dealWhatif(dealId, incFrac, attachEff, filters).then(setPreview);
    }, 150);
    return () => clearTimeout(t);
  }, [incFrac, attachEff, saved]);

  const dirty = saved && (Math.abs(incFrac - saved.incremental_fraction) > 0.001 ||
    Math.abs(attachEff - saved.attach_effect) > 0.001);

  const handleSave = async () => {
    setSaving(true);
    const updated = await api.updateDealAssumptions(dealId, {
      incremental_fraction: incFrac,
      attach_effect: attachEff,
    });
    setSaved(updated);
    setPreview(updated);
    setSaving(false);
    onSaved();
  };

  if (!saved || !preview) {
    return (
      <Card className="lg:col-span-3">
        <div className="py-16 text-center font-mono text-text-tertiary">Loading…</div>
      </Card>
    );
  }

  return (
    <Card
      title={saved.name}
      subtitle={`Code ${saved.code} · ${saved.redemptions} redemptions this period`}
      className="lg:col-span-3"
      emphasis
    >
      <p className="text-[13.5px] leading-relaxed text-text-secondary">{preview.verdict}</p>

      <div className="mt-4 grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
        <div>
          <div className="mb-1.5 flex items-center justify-between font-mono text-[12px] text-text-secondary">
            <span>Orders you&rsquo;d have gotten anyway</span>
            <span className="text-text-primary">{pct(100 - incFrac * 100, 0)}</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={incFrac}
            onChange={(e) => setIncFrac(Number(e.target.value))}
            className="w-full accent-[var(--accent)]"
          />
          <div className="mt-1 font-mono text-[10.5px] text-text-tertiary">
            {pct(incFrac * 100, 0)} were genuinely new business
          </div>
        </div>
        <div>
          <div className="mb-1.5 flex items-center justify-between font-mono text-[12px] text-text-secondary">
            <span>Add-ons this deal pulls in</span>
            <span className="text-text-primary">{pct(attachEff * 100, 0)}</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={attachEff}
            onChange={(e) => setAttachEff(Number(e.target.value))}
            className="w-full accent-[var(--accent)]"
          />
          <div className="mt-1 font-mono text-[10.5px] text-text-tertiary">drinks, wings, sides</div>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4 border-t border-border pt-4">
        <Metric label="Revenue" value={money(saved.revenue)} />
        <Metric label="Discount given" value={money(saved.discount_given)} />
        <Metric label="Cost to make" value={money(saved.food_cost)} />
        <Metric
          label="True profit (live)"
          value={money(preview.true_profit)}
          tone={preview.true_profit >= 0 ? "profit" : "loss"}
        />
      </div>

      {dirty && (
        <div className="mt-4 flex items-center gap-3 border-t border-border pt-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-accent px-4 py-2 font-mono text-[12.5px] font-medium text-[#1a1305] hover:bg-accent/90 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save these assumptions"}
          </button>
          <button
            onClick={() => {
              setIncFrac(saved.incremental_fraction);
              setAttachEff(saved.attach_effect);
            }}
            className="font-mono text-[12.5px] text-text-tertiary hover:text-text-secondary"
          >
            Revert
          </button>
        </div>
      )}
    </Card>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "profit" | "loss" }) {
  return (
    <div>
      <div className="font-mono text-[11px] text-text-tertiary">{label}</div>
      <div
        className="mt-0.5 font-mono text-[15px] font-medium"
        style={{ color: tone === "profit" ? "var(--profit)" : tone === "loss" ? "var(--loss)" : "var(--text-primary)" }}
      >
        {value}
      </div>
    </div>
  );
}
