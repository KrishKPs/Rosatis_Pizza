import type {
  CategoryBreakdown,
  ChannelBreakdown,
  CountSession,
  CountSheetResponse,
  CustomerRow,
  CustomerSummary,
  DealStats,
  HeatCell,
  InventoryItem,
  InventoryResponse,
  Meta,
  MenuItemRow,
  OrderRow,
  SalesSummary,
  TimeseriesPoint,
  TopItem,
  UsageDay,
} from "./types";

const BASE = "/api";

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const qs = params
    ? "?" +
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== "")
        .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
        .join("&")
    : "";
  const res = await fetch(`${BASE}${path}${qs}`);
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

export interface Filters {
  start?: string;
  end?: string;
  channel?: string;
  [key: string]: string | number | undefined;
}

export const api = {
  meta: () => get<Meta>("/meta"),
  resetOverrides: () => post<{ status: string }>("/meta/reset"),

  salesSummary: (f: Filters) => get<SalesSummary>("/sales/summary", f),
  salesTimeseries: (f: Filters) => get<TimeseriesPoint[]>("/sales/timeseries", f),
  salesByCategory: (f: Filters) => get<CategoryBreakdown[]>("/sales/by-category", f),
  salesByChannel: (f: Filters) => get<ChannelBreakdown[]>("/sales/by-channel", f),
  salesHeatmap: (f: Filters) => get<HeatCell[]>("/sales/heatmap", f),
  salesTopItems: (f: Filters, n = 10) => get<TopItem[]>("/sales/top-items", { ...f, n }),

  deals: (f: Filters) => get<DealStats[]>("/deals", f),
  deal: (id: string, f: Filters) => get<DealStats>(`/deals/${id}`, f),
  dealWhatif: (id: string, incremental_fraction: number, attach_effect: number, f: Filters) =>
    get<DealStats>(`/deals/${id}/whatif`, { ...f, incremental_fraction, attach_effect }),
  updateDealAssumptions: (id: string, body: { incremental_fraction?: number; attach_effect?: number }) =>
    patch<DealStats>(`/deals/${id}/assumptions`, body),

  inventory: () => get<InventoryResponse>("/inventory"),
  inventoryUsage: (days = 14) => get<UsageDay[]>("/inventory/usage", { days }),
  updateIngredient: (id: string, unit_cost: number) =>
    patch<InventoryItem>(`/inventory/${id}`, { unit_cost }),

  countSheet: () => get<CountSheetResponse>("/inventory/count-sheet"),
  countHistory: (limit = 20) => get<CountSession[]>("/inventory/count-history", { limit }),
  submitCount: (body: { counted_by: string; entries: { ingredient_id: string; counted_qty: number }[]; note?: string }) =>
    post<CountSheetResponse>("/inventory/count", body),

  menu: (category?: string) => get<MenuItemRow[]>("/menu", { category }),
  categories: () => get<string[]>("/menu/categories"),
  updateMenuItem: (
    id: string,
    body: { price?: number; food_cost?: number; reset_food_cost?: boolean },
  ) => patch<MenuItemRow>(`/menu/${id}`, body),

  orders: (f: Filters, limit = 50) => get<OrderRow[]>("/orders", { ...f, limit }),
  ordersByChannel: (f: Filters) => get<ChannelBreakdown[]>("/orders/channels", f),

  customerSummary: (f: Filters) => get<CustomerSummary>("/customers/summary", f),
  topCustomers: (n = 10, by = "total_spent") => get<CustomerRow[]>("/customers/top", { n, by }),
  customers: () => get<CustomerRow[]>("/customers"),
};
