import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { MenuItemRow } from "../api/types";
import { useFilters } from "../context/FiltersContext";
import { TopBar } from "../components/layout/TopBar";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { money, pct } from "../lib/format";

type SortKey = "margin_pct" | "price" | "food_cost" | "name";

export function MenuPage() {
  const { refreshKey } = useFilters();
  const [items, setItems] = useState<MenuItemRow[]>([]);
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>("margin_pct");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);
  const [loading, setLoading] = useState(true);
  const [editingField, setEditingField] = useState<{ id: string; field: "price" | "food_cost" } | null>(null);
  const [editValue, setEditValue] = useState("");

  const load = () => {
    setLoading(true);
    Promise.all([api.menu(category || undefined), api.categories()]).then(([m, c]) => {
      setItems(m);
      setCategories(c);
      setLoading(false);
    });
  };

  useEffect(load, [category, refreshKey]);

  const sorted = useMemo(() => {
    const arr = [...items];
    arr.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string") return sortDir * av.localeCompare(bv as string);
      return sortDir * ((av as number) - (bv as number));
    });
    return arr;
  }, [items, sortKey, sortDir]);

  const highest = items.length ? items.reduce((a, b) => (a.margin_pct > b.margin_pct ? a : b)) : null;
  const lowest = items.length ? items.reduce((a, b) => (a.margin_pct < b.margin_pct ? a : b)) : null;
  const avgMargin = items.length ? items.reduce((s, i) => s + i.margin_pct, 0) / items.length : 0;

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) setSortDir((d) => (d === 1 ? -1 : 1));
    else {
      setSortKey(key);
      setSortDir(-1);
    }
  };

  const startEdit = (id: string, field: "price" | "food_cost", current: number) => {
    setEditingField({ id, field });
    setEditValue(String(current));
  };

  const commitEdit = async () => {
    if (!editingField) return;
    const val = parseFloat(editValue);
    setEditingField(null);
    if (Number.isNaN(val) || val < 0) return;
    await api.updateMenuItem(editingField.id, { [editingField.field]: val });
    load();
  };

  const resetFoodCost = async (id: string) => {
    await api.updateMenuItem(id, { reset_food_cost: true });
    load();
  };

  return (
    <div>
      <TopBar
        title="Menu & Pricing"
        subtitle="What should this cost?"
        showFilters={false}
        right={
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-lg border border-border bg-surface-1 px-3 py-2 font-mono text-[12.5px] text-text-primary outline-none"
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        }
      />
      <div className="px-4 py-4 md:px-8 md:py-6">
        {loading ? (
          <div className="py-24 text-center font-mono text-text-tertiary">Loading…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
              <StatCard label="Average profit per item" value={pct(avgMargin)} />
              <StatCard
                label="Highest margin"
                value={highest ? `${highest.name} (${pct(highest.margin_pct)})` : "–"}
                tone="profit"
              />
              <StatCard
                label="Lowest margin"
                value={lowest ? `${lowest.name} (${pct(lowest.margin_pct)})` : "–"}
                tone="loss"
              />
              <StatCard label="Menu items" value={items.length.toString()} />
            </div>

            <div className="mt-4">
              <Card title="Full menu" subtitle="Click a price or cost to edit it — margins update everywhere instantly">
                <div className="overflow-x-auto"><table className="w-full min-w-[660px]">
                  <thead>
                    <tr className="border-b border-border text-left font-mono text-[11px] text-text-tertiary">
                      <SortTh label="Item" active={sortKey === "name"} dir={sortDir} onClick={() => toggleSort("name")} />
                      <th className="pb-2 font-medium">Category</th>
                      <SortTh
                        label="Price"
                        align="right"
                        active={sortKey === "price"}
                        dir={sortDir}
                        onClick={() => toggleSort("price")}
                      />
                      <SortTh
                        label="Cost to make"
                        align="right"
                        active={sortKey === "food_cost"}
                        dir={sortDir}
                        onClick={() => toggleSort("food_cost")}
                      />
                      <th className="pb-2 text-right font-medium">Profit per item</th>
                      <SortTh
                        label="Margin"
                        align="right"
                        active={sortKey === "margin_pct"}
                        dir={sortDir}
                        onClick={() => toggleSort("margin_pct")}
                      />
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((item) => (
                      <tr key={item.item_id} className="border-b border-border/60 last:border-0 hover:bg-surface-2">
                        <td className="py-2 text-[13px] text-text-primary">{item.name}</td>
                        <td className="py-2 font-mono text-[12px] text-text-tertiary">{item.category}</td>
                        <td className="py-2 text-right font-mono text-[12.5px]">
                          <EditableCell
                            editing={editingField?.id === item.item_id && editingField.field === "price"}
                            value={editValue}
                            display={money(item.price, { cents: true })}
                            onStart={() => startEdit(item.item_id, "price", item.price)}
                            onChange={setEditValue}
                            onCommit={commitEdit}
                          />
                        </td>
                        <td className="py-2 text-right font-mono text-[12.5px]">
                          <EditableCell
                            editing={editingField?.id === item.item_id && editingField.field === "food_cost"}
                            value={editValue}
                            display={money(item.food_cost, { cents: true })}
                            overridden={item.food_cost_overridden}
                            onStart={() => startEdit(item.item_id, "food_cost", item.food_cost)}
                            onChange={setEditValue}
                            onCommit={commitEdit}
                            onReset={item.food_cost_overridden ? () => resetFoodCost(item.item_id) : undefined}
                          />
                        </td>
                        <td className="py-2 text-right font-mono text-[12.5px] text-text-primary">
                          {money(item.margin, { cents: true })}
                        </td>
                        <td className="py-2 text-right">
                          <span
                            className="font-mono text-[12.5px] font-medium"
                            style={{
                              color:
                                item.margin_pct >= 65
                                  ? "var(--profit)"
                                  : item.margin_pct < 40
                                    ? "var(--loss)"
                                    : "var(--text-primary)",
                            }}
                          >
                            {pct(item.margin_pct)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function SortTh({
  label,
  active,
  dir,
  onClick,
  align = "left",
}: {
  label: string;
  active: boolean;
  dir: 1 | -1;
  onClick: () => void;
  align?: "left" | "right";
}) {
  return (
    <th
      onClick={onClick}
      className={`cursor-pointer pb-2 font-medium hover:text-text-secondary ${align === "right" ? "text-right" : "text-left"}`}
    >
      {label} {active && (dir === 1 ? "↑" : "↓")}
    </th>
  );
}

function EditableCell({
  editing,
  value,
  display,
  overridden,
  onStart,
  onChange,
  onCommit,
  onReset,
}: {
  editing: boolean;
  value: string;
  display: string;
  overridden?: boolean;
  onStart: () => void;
  onChange: (v: string) => void;
  onCommit: () => void;
  onReset?: () => void;
}) {
  if (editing) {
    return (
      <input
        autoFocus
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onCommit}
        onKeyDown={(e) => e.key === "Enter" && onCommit()}
        className="w-20 rounded border border-accent/40 bg-surface-2 px-1.5 py-0.5 text-right text-text-primary outline-none"
      />
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5">
      {overridden && <span title="Owner-edited, no longer from the recipe" className="text-accent">●</span>}
      <button onClick={onStart} className="text-text-secondary underline decoration-dotted underline-offset-2 hover:text-accent">
        {display}
      </button>
      {onReset && (
        <button onClick={onReset} title="Revert to recipe-based cost" className="text-text-tertiary hover:text-text-secondary">
          ↺
        </button>
      )}
    </span>
  );
}
