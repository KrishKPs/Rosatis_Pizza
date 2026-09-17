export interface Meta {
  date_min: string;
  date_max: string;
  channels: { id: string; name: string; commission: number }[];
  categories: string[];
  store_name: string;
  store_address: string;
}

export interface SalesSummary {
  revenue: number;
  order_count: number;
  net_profit: number;
  net_margin_pct: number;
  avg_order_value: number;
}

export interface TimeseriesPoint {
  date: string;
  revenue: number;
  net_profit: number;
  order_count: number;
}

export interface CategoryBreakdown {
  category: string;
  revenue: number;
  profit: number;
}

export interface ChannelBreakdown {
  channel_id: string;
  channel_name: string;
  commission_pct: number;
  revenue: number;
  net_profit: number;
  net_margin_pct: number;
  order_count: number;
}

export interface HeatCell {
  weekday: number;
  hour: number;
  orders: number;
  revenue: number;
}

export interface TopItem {
  item_id: string;
  name: string;
  category: string;
  qty_sold: number;
  revenue: number;
}

export interface DealStats {
  deal_id: string;
  name: string;
  code: string;
  type: string;
  availability: string;
  redemptions: number;
  revenue: number;
  discount_given: number;
  food_cost: number;
  commission: number;
  attach_revenue: number;
  actual_profit: number;
  incremental_fraction: number;
  attach_effect: number;
  baseline_profit_per_order: number;
  margin_given_away: number;
  attach_bonus: number;
  true_profit: number;
  true_profit_per_redemption: number;
  verdict: string;
}

export interface InventoryItem {
  ingredient_id: string;
  name: string;
  unit: string;
  kind: "food" | "packaging" | "supply";
  stock_level: number;
  unit_cost: number;
  reorder_point: number;
  restock_to: number;
  value: number;
  status: "ok" | "low" | "out";
  low_stock: boolean;
}

export interface InventoryResponse {
  kpis: {
    items_low_or_out: number;
    items_out: number;
    total_inventory_value: number;
  };
  items: InventoryItem[];
}

export interface UsageDay {
  date: string;
  usage: Record<string, number>;
}

export type CountStatus = "ok" | "low" | "out" | "uncounted";

export interface CountSheetItem {
  ingredient_id: string;
  name: string;
  unit: string;
  kind: "food" | "packaging" | "supply";
  unit_cost: number;
  reorder_point: number;
  restock_to: number;
  system_expected: number | null;
  last_count_qty: number | null;
  last_counted_at: string | null;
  last_counted_by: string | null;
  on_hand: number | null;
  variance: number | null;
  status: CountStatus;
  suggested_order_qty: number | null;
}

export interface ReorderRow {
  ingredient_id: string;
  name: string;
  unit: string;
  kind: "food" | "packaging" | "supply";
  on_hand: number | null;
  reorder_point: number;
  suggested_order_qty: number | null;
  status: CountStatus;
}

export interface CountSheetResponse {
  kpis: {
    items_to_reorder: number;
    items_out: number;
    items_never_counted: number;
    last_session_at: string | null;
    last_session_by: string | null;
  };
  items: CountSheetItem[];
  reorder_list: ReorderRow[];
}

export interface CountSession {
  id: string;
  counted_at: string;
  counted_by: string;
  note: string | null;
  items_counted: number;
}

export interface MenuItemRow {
  item_id: string;
  name: string;
  category: string;
  price: number;
  price_src: "real" | "filled";
  food_cost: number;
  food_cost_overridden: boolean;
  margin: number;
  margin_pct: number;
}

export interface OrderRow {
  order_id: string;
  timestamp: string;
  channel: string;
  channel_name: string;
  customer_name: string;
  items: { item_id: string; name: string; qty: number }[];
  deal_id: string | null;
  deal_name: string | null;
  revenue: number;
  food_cost: number;
  commission_paid: number;
  net_profit: number;
}

export interface CustomerSummary {
  total_customers: number;
  repeat_customers: number;
  repeat_rate_pct: number;
  avg_visits: number;
  loyalty_points_outstanding: number;
}

export interface CustomerRow {
  customer_id: string;
  name: string;
  first_order_date: string;
  order_count: number;
  total_spent: number;
  loyalty_points: number;
  is_repeat: boolean;
}
