"""
data.py — the single seeded data foundation for Rosati's Ops (Raleigh).

Everything the app shows is generated here, reproducibly (fixed seed). Real menu
items and prices from the Raleigh store; gaps filled with realistic values and
marked FILLED. Every cost is a default and EDITABLE — the owner's real numbers can
replace them without touching any other file.

Nothing here is decorative: sales, deal profit, channel profit, and inventory
depletion are all computed from the ORDERS generated at the bottom.

Run `python3 data.py` to print a sanity summary.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

SEED = 1964  # Rosati's founding year; fixed so the demo is identical every run
rng = random.Random(SEED)

# Tag helper: mark whether a number is REAL (from the live menu) or FILLED (realistic default)
REAL = "real"
FILLED = "filled"

# ---------------------------------------------------------------------------
# 1. INGREDIENTS  (raw + prepped stock)  — unit_cost EDITABLE
# ---------------------------------------------------------------------------
@dataclass
class Ingredient:
    id: str
    name: str
    unit: str              # how we count it
    unit_cost: float       # $ per unit — EDITABLE
    stock: float           # current on hand (set well-stocked in §7)
    reorder_point: float   # trips a low-stock alert
    restock_to: float      # level a restock refills to

# quantities are plausible, not exact-to-the-gram
INGREDIENTS: dict[str, Ingredient] = {i.id: i for i in [
    Ingredient("dough",     "Dough (per oz)",        "oz",   0.04,  9000, 2500, 9000),
    Ingredient("mozz",      "Mozzarella (per oz)",   "oz",   0.28,  7000, 2000, 7000),
    Ingredient("sauce",     "Pizza sauce (per oz)",  "oz",   0.06,  6000, 1500, 6000),
    Ingredient("pepperoni", "Pepperoni (per oz)",    "oz",   0.35,  1800,  500, 1800),
    Ingredient("sausage",   "Italian sausage (oz)",  "oz",   0.30,  1600,  450, 1600),
    Ingredient("beef",      "Italian beef (oz)",     "oz",   0.38,   900,  250,  900),
    Ingredient("veggies",   "Veggie mix (per oz)",   "oz",   0.10,  2000,  500, 2000),
    Ingredient("pineapple", "Pineapple/ham (oz)",    "oz",   0.16,   700,  200,  700),
    Ingredient("wings",     "Jumbo wings (each)",    "each", 0.42,  1400,  400, 1400),
    Ingredient("pasta",     "Pasta (per oz)",        "oz",   0.05,  2400,  600, 2400),
    Ingredient("alfredo",   "Alfredo sauce (oz)",    "oz",   0.09,   900,  250,  900),
    Ingredient("chicken",   "Grilled chicken (oz)",  "oz",   0.34,   900,  250,  900),
    Ingredient("marinara",  "Marinara (per oz)",     "oz",   0.05,  1200,  300, 1200),
    Ingredient("meatball",  "Meatballs (each)",      "each", 0.55,   500,  150,  500),
    Ingredient("subroll",   "Sub roll (each)",       "each", 0.45,   500,  150,  500),
    Ingredient("lettuce",   "Lettuce/salad mix (oz)","oz",   0.07,  1500,  400, 1500),
    Ingredient("cheese_bl", "Cheese blend (oz)",     "oz",   0.26,  1000,  300, 1000),
    Ingredient("gfcrust",   "Gluten-free crust (ea)","each", 1.80,   200,   60,  200),
    Ingredient("soda2l",    "Soda 2L (each)",        "each", 1.10,   400,  120,  400),
    Ingredient("can",       "Canned soda (each)",    "each", 0.35,   800,  200,  800),
    Ingredient("dessert",   "Dessert unit (each)",   "each", 1.20,   300,   90,  300),
    Ingredient("box",       "Pizza box (each)",      "each", 0.35,  2500,  700, 2500),
]}

# ---------------------------------------------------------------------------
# 2. MENU  — real prices where found (REAL), realistic fills (FILLED)
#    food_cost is DERIVED from the recipe (§3), never typed by hand.
# ---------------------------------------------------------------------------
@dataclass
class MenuItem:
    id: str
    name: str
    category: str
    price: float
    price_src: str                     # REAL or FILLED
    recipe: dict[str, float]           # ingredient_id -> qty consumed
    food_cost: float = 0.0             # filled in by compute_food_costs()
    @property
    def margin(self) -> float:
        return round(self.price - self.food_cost, 2)
    @property
    def margin_pct(self) -> float:
        return round(100 * self.margin / self.price, 1) if self.price else 0.0

# --- Pizza recipe helper: cheese pizza by diameter, +toppings added per item ---
# oz of dough/cheese/sauce scale with pizza size; a box each.
PIZZA_BASE = {  # diameter(in): (dough_oz, mozz_oz, sauce_oz)
    10: (10, 6, 4), 12: (14, 8, 5), 14: (20, 11, 7), 16: (26, 14, 9), 18: (32, 18, 11),
}
def pizza_recipe(diam, toppings: dict[str, float] | None = None):
    d, m, s = PIZZA_BASE[diam]
    r = {"dough": d, "mozz": m, "sauce": s, "box": 1}
    if toppings:
        for k, v in toppings.items():
            r[k] = r.get(k, 0) + v
    return r

MENU: list[MenuItem] = []

# Build-Your-Own (cheese base) — REAL prices; crust variants priced off base
BYO_PRICE = {12: 15.99, 14: 18.99, 16: 20.99, 18: 22.99}   # REAL (thin)
# Chicago Style (deep) — REAL where known, FILLED for missing sizes
DEEP_PRICE = {10: 17.99, 12: 20.49, 14: 21.99, 16: 24.49, 18: 27.49}  # 10&14 REAL, others FILLED
DOUBLE_PRICE = {12: 21.99, 14: 23.49, 16: 25.99, 18: 28.99}  # FILLED (double dough premium)

def add_pizza(pid, name, cat, price, src, diam, toppings=None):
    MENU.append(MenuItem(pid, name, cat, price, src, pizza_recipe(diam, toppings)))

# Full size x crust matrix for Build-Your-Own cheese
for diam, base in BYO_PRICE.items():
    add_pizza(f"byo_thin_{diam}", f'{diam}" Build-Your-Own — Thin Crust', "Pizza", base, REAL, diam)
    add_pizza(f"byo_deep_{diam}", f'{diam}" Build-Your-Own — Deep Dish', "Pizza",
              round(base + 2.00, 2), FILLED, diam, {"mozz": 4})   # deep uses more cheese
    add_pizza(f"byo_dbl_{diam}",  f'{diam}" Build-Your-Own — Double Dough', "Pizza",
              round(base + 3.00, 2), FILLED, diam, {"dough": PIZZA_BASE[diam][0]*0.5})
# Chicago Style (deep) at its known sizes
for diam, price in DEEP_PRICE.items():
    src = REAL if diam in (10, 14) else FILLED
    add_pizza(f"chi_{diam}", f'{diam}" Chicago Style', "Pizza", price, src, diam, {"mozz": 4, "sauce": 2})

# Named specialty pizzas — REAL prices where found; toppings drive cost
add_pizza("spec_monster_18", '18" Rosati\'s Monster', "Pizza", 34.99, REAL, 18,
          {"pepperoni": 4, "sausage": 4, "beef": 3, "veggies": 3})
add_pizza("spec_monster_14", '14" Rosati\'s Monster', "Pizza", 28.99, REAL, 14,
          {"pepperoni": 3, "sausage": 3, "beef": 2, "veggies": 2})
add_pizza("spec_monster_12", '12" Rosati\'s Monster', "Pizza", 25.99, REAL, 12,
          {"pepperoni": 2, "sausage": 2, "beef": 2, "veggies": 2})
add_pizza("spec_meat_18",   '18" Meat Mania', "Pizza", 31.99, REAL, 18,
          {"pepperoni": 4, "sausage": 4, "beef": 3})
add_pizza("spec_four_16",   '16" Fabulous Four', "Pizza", 27.99, REAL, 16,
          {"pepperoni": 3, "sausage": 3, "veggies": 2})
add_pizza("spec_veg_16",    '16" Veggie', "Pizza", 25.99, REAL, 16, {"veggies": 5})
add_pizza("spec_combo_14",  '14" Classic Combo', "Pizza", 25.99, REAL, 14,
          {"pepperoni": 3, "sausage": 3})
add_pizza("spec_combo_12",  '12" Classic Combo', "Pizza", 20.99, REAL, 12,
          {"pepperoni": 2, "sausage": 2})
add_pizza("spec_haw_12",    '12" Hawaiian', "Pizza", 19.99, REAL, 12, {"pineapple": 3})
add_pizza("spec_white_12",  '12" White', "Pizza", 19.99, REAL, 12, {"mozz": 4})
add_pizza("gf_10",          '10" Gluten Free', "Pizza", 12.99, REAL, 10, {"gfcrust": 1})

# Wings — REAL 12ct; FILLED sizes
MENU += [
    MenuItem("wings_12", "12 Jumbo Wings", "Wings", 18.99, REAL, {"wings": 12}),
    MenuItem("wings_18", "18 Jumbo Wings", "Wings", 26.99, FILLED, {"wings": 18}),
    MenuItem("wings_6",  "6 Jumbo Wings",  "Wings", 10.99, FILLED, {"wings": 6}),
    MenuItem("wings_bl", "Boneless Wings (10)", "Wings", 11.99, FILLED, {"chicken": 8}),
]

# Pasta — REAL prices
MENU += [
    MenuItem("pasta_alfredo", "Fettuccine Alfredo w/ Grilled Chicken", "Pastas", 14.49, REAL,
             {"pasta": 8, "alfredo": 5, "chicken": 5}),
    MenuItem("pasta_parm",    "Chicken Parmigiana", "Pastas", 14.49, REAL,
             {"pasta": 8, "marinara": 5, "chicken": 5, "mozz": 3}),
    MenuItem("pasta_penne",   "Three Cheese Baked Penne", "Pastas", 15.49, REAL,
             {"pasta": 9, "marinara": 5, "cheese_bl": 4}),
    MenuItem("pasta_spag",    "Spaghetti & Meatball", "Pastas", 14.49, REAL,
             {"pasta": 8, "marinara": 5, "meatball": 3}),
    MenuItem("pasta_byo",     "Build-Your-Own Pasta", "Pastas", 14.49, REAL,
             {"pasta": 8, "marinara": 5}),
]

# Sandwiches — REAL
MENU += [
    MenuItem("sand_beef",    "Italian Beef Sandwich", "Sandwiches", 10.99, REAL,
             {"subroll": 1, "beef": 6}),
    MenuItem("sand_sausage", "Italian Sausage Sandwich", "Sandwiches", 9.99, REAL,
             {"subroll": 1, "sausage": 5}),
    MenuItem("sand_meatball","Meatball Sandwich", "Sandwiches", 10.49, FILLED,
             {"subroll": 1, "meatball": 3, "marinara": 3}),
]

# Salads — Garden REAL; others FILLED
MENU += [
    MenuItem("salad_garden", "Garden Salad", "Salads", 9.99, REAL, {"lettuce": 8, "veggies": 3}),
    MenuItem("salad_caesar", "Caesar Salad", "Salads", 9.49, FILLED, {"lettuce": 8, "cheese_bl": 1}),
    MenuItem("salad_chicken","Chicken Caesar Salad", "Salads", 12.49, FILLED,
             {"lettuce": 8, "chicken": 5, "cheese_bl": 1}),
]

# Calzone — REAL
MENU += [
    MenuItem("calzone", "Calzone", "Calzone", 12.99, REAL, {"dough": 16, "mozz": 8, "sauce": 3, "box": 1}),
]

# Appetizers — FILLED (prices not listed online)
MENU += [
    MenuItem("app_bread",   "Garlic Bread", "Appetizers", 6.99, FILLED, {"dough": 8, "mozz": 3}),
    MenuItem("app_cheese",  "Cheese Bread", "Appetizers", 8.49, FILLED, {"dough": 10, "mozz": 6}),
    MenuItem("app_sticks",  "Mozzarella Sticks", "Appetizers", 8.99, FILLED, {"cheese_bl": 6}),
]

# Desserts — FILLED
MENU += [
    MenuItem("des_cannoli", "Cannoli", "Desserts", 5.99, FILLED, {"dessert": 1}),
    MenuItem("des_brownie", "Chocolate Brownie", "Desserts", 5.49, FILLED, {"dessert": 1}),
]

# Beverages — FILLED
MENU += [
    MenuItem("bev_2l",  "2-Liter Soda", "Beverages", 3.99, FILLED, {"soda2l": 1}),
    MenuItem("bev_can", "Canned Soda",  "Beverages", 1.99, FILLED, {"can": 1}),
]

MENU_BY_ID = {m.id: m for m in MENU}

def compute_food_costs():
    """Derive each item's food_cost from its recipe + ingredient unit costs.
    One source of truth: the same recipe drives cost AND inventory depletion."""
    for m in MENU:
        m.food_cost = round(sum(INGREDIENTS[iid].unit_cost * qty
                                for iid, qty in m.recipe.items()), 2)
compute_food_costs()

# ---------------------------------------------------------------------------
# 3. CHANNELS  — commission EDITABLE
# ---------------------------------------------------------------------------
@dataclass
class Channel:
    id: str
    name: str
    commission: float   # fraction the platform takes (0 for in-house)

CHANNELS: dict[str, Channel] = {c.id: c for c in [
    Channel("dinein",   "Dine-In",         0.00),
    Channel("carryout", "Carryout",        0.00),
    Channel("delivery", "In-House Delivery",0.00),
    Channel("doordash", "DoorDash",        0.25),
    Channel("ubereats", "Uber Eats",       0.25),
    Channel("grubhub",  "Grubhub",         0.20),
]}
CHANNEL_IDS = list(CHANNELS)  # even split target

# ---------------------------------------------------------------------------
# 4. DEALS  — the 6 real ones. incremental_fraction & attach_effect are MODELED
#    assumptions, EDITABLE. popularity_weight sets how often each is chosen.
# ---------------------------------------------------------------------------
@dataclass
class Deal:
    id: str
    name: str
    code: str
    type: str                   # percent | free_item | bogo | bundle
    popularity_weight: float    # relative share among deal-using orders
    incremental_fraction: float # of these orders, share that are truly NEW business
    attach_effect: float        # tendency to pull extra add-ons (0..1)
    availability: str           # 'daily' or a weekday name
    params: dict = field(default_factory=dict)

DEALS: dict[str, Deal] = {d.id: d for d in [
    Deal("bogo",      "BOGO — Buy 1 Pizza Get 1 Free", "BOGO", "bogo", 0.34, 0.35, 0.30, "daily",
         {"note": "second pizza free, equal or lesser value"}),
    Deal("family",    "Family Deal", "FAMILY", "bundle", 0.22, 0.55, 0.60, "daily",
         {"price": 58.99, "contents": "two 18\" 1-topping + 12 wings"}),
    Deal("pizzanight","Pizza Night", "PIZZANIGHT", "bundle", 0.16, 0.50, 0.35, "daily",
         {"price": 38.99, "contents": "two 18\" 1-topping pizzas"}),
    Deal("tenoff",    "10% Off $20+", "10OFF", "percent", 0.14, 0.40, 0.20, "daily",
         {"percent": 0.10, "min_subtotal": 20}),
    Deal("free12",    "Free 12\" with 18\"", "FREE12", "free_item", 0.09, 0.45, 0.40, "daily",
         {"free_item": "byo_thin_12", "requires_18": True}),
    Deal("wednesday", "Wednesday 2 Pastas $21", "WEDNESDAY", "bundle", 0.05, 0.50, 0.30, "Wednesday",
         {"price": 21.00, "contents": "any 2 pastas"}),
]}

# ---------------------------------------------------------------------------
# 5. CUSTOMERS  — sized to a modest store; repeat vs new + loyalty points
# ---------------------------------------------------------------------------
FIRST_NAMES = ["James","Maria","David","Linda","Robert","Patricia","John","Jennifer",
    "Michael","Elizabeth","Chris","Susan","Tony","Angela","Mark","Nancy","Paul","Karen",
    "Steve","Lisa","Kevin","Donna","Brian","Sandra","Jason","Amy","Eric","Rachel"]
LAST_NAMES = ["Smith","Johnson","Rossi","Brown","Davis","Miller","Wilson","Moore",
    "Taylor","Anderson","Romano","Ricci","Nguyen","Patel","Garcia","Martin","Lee","Clark"]

@dataclass
class Customer:
    id: str
    name: str
    first_order_date: date
    order_count: int = 0
    total_spent: float = 0.0
    loyalty_points: int = 0
    @property
    def is_repeat(self) -> bool:
        return self.order_count > 1

N_CUSTOMERS = 55   # modest store, readable loyalty list
START = date(2026, 8, 10)   # a Monday; 4 weeks of history
DAYS = 28

CUSTOMERS: list[Customer] = []
for i in range(N_CUSTOMERS):
    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    fo = START + timedelta(days=rng.randint(0, DAYS - 1))
    CUSTOMERS.append(Customer(f"cust_{i:03d}", name, fo))
# a core of regulars order much more often than one-timers
REGULARS = CUSTOMERS[:18]

# ---------------------------------------------------------------------------
# 6. ORDER GENERATION  — tuned to real daily revenue targets
#    weekends ~$1100-1200/day, weekdays ~$600-700/day, ~$28 avg order,
#    weekends skew to BIGGER family orders, deals common, BOGO most popular.
# ---------------------------------------------------------------------------
@dataclass
class OrderLine:
    item_id: str
    qty: int

@dataclass
class Order:
    id: str
    ts: datetime
    channel: str
    customer_id: str
    lines: list[OrderLine]
    deal_id: str | None
    revenue: float
    food_cost: float
    commission_paid: float
    net_profit: float

PIZZAS = [m.id for m in MENU if m.category == "Pizza"]
SIDES  = [m.id for m in MENU if m.category in ("Wings","Appetizers","Salads")]
DRINKS = [m.id for m in MENU if m.category == "Beverages"]
PASTAS = [m.id for m in MENU if m.category == "Pastas"]
DESSERTS = [m.id for m in MENU if m.category == "Desserts"]

def _weighted_deal(is_wed: bool):
    pool = [d for d in DEALS.values() if d.availability == "daily" or (is_wed and d.availability == "Wednesday")]
    return rng.choices(pool, weights=[d.popularity_weight for d in pool])[0]

def _build_basket(weekend: bool):
    """Return list[OrderLine] roughly matching ~$28 avg, bigger on weekends."""
    lines = []
    n_pizza = rng.choice([1,1,2] if not weekend else [1,2,2,3])  # weekends = family
    for _ in range(n_pizza):
        lines.append(OrderLine(rng.choice(PIZZAS), 1))
    if rng.random() < (0.75 if weekend else 0.45):
        lines.append(OrderLine(rng.choice(SIDES), 1))
    if rng.random() < (0.7 if weekend else 0.5):
        lines.append(OrderLine(rng.choice(DRINKS), rng.choice([1,1,2])))
    if weekend and rng.random() < 0.3:
        lines.append(OrderLine(rng.choice(DESSERTS), 1))
    if rng.random() < 0.15:
        lines.append(OrderLine(rng.choice(PASTAS), 1))
    return lines

def _price_basket(lines):
    return round(sum(MENU_BY_ID[l.item_id].price * l.qty for l in lines), 2)

def _apply_deal(lines, deal):
    """Return (revenue_delta, note) approximating each deal's discount."""
    subtotal = _price_basket(lines)
    if deal.type == "percent" and subtotal >= deal.params.get("min_subtotal", 0):
        return -round(subtotal * deal.params["percent"], 2)
    if deal.type == "bogo":
        pizza_prices = sorted([MENU_BY_ID[l.item_id].price for l in lines
                               if MENU_BY_ID[l.item_id].category == "Pizza"])
        if len(pizza_prices) >= 2:
            return -pizza_prices[0]  # cheapest pizza free
        return 0.0
    if deal.type == "free_item":
        has18 = any('18"' in MENU_BY_ID[l.item_id].name for l in lines)
        if has18:
            return -MENU_BY_ID[deal.params["free_item"]].price
        return 0.0
    if deal.type == "bundle":
        return round(deal.params["price"] - subtotal, 2)  # usually negative
    return 0.0

def generate_orders():
    orders: list[Order] = []
    oid = 0
    for day_i in range(DAYS):
        d = START + timedelta(days=day_i)
        weekend = d.weekday() >= 4  # Fri/Sat/Sun busier
        is_wed = d.weekday() == 2
        target = rng.uniform(1100, 1200) if weekend else rng.uniform(600, 700)
        day_total = 0.0
        guard = 0
        while day_total < target and guard < 200:
            guard += 1
            weekend_basket = weekend
            lines = _build_basket(weekend_basket)
            revenue = _price_basket(lines)
            deal = None
            deal_delta = 0.0
            if rng.random() < 0.55:  # deals are COMMON
                deal = _weighted_deal(is_wed)
                deal_delta = _apply_deal(lines, deal)
            revenue = round(revenue + deal_delta, 2)
            if revenue <= 0:
                continue
            channel = rng.choice(CHANNEL_IDS)  # even split
            fc = round(sum(MENU_BY_ID[l.item_id].food_cost * l.qty for l in lines), 2)
            comm = round(revenue * CHANNELS[channel].commission, 2)
            net = round(revenue - fc - comm, 2)
            # order time within service hours, clustered at lunch & dinner
            hour = rng.choice([11,12,12,13,17,18,18,19,19,20]) if weekend else rng.choice([11,12,13,17,18,19,20])
            ts = datetime(d.year, d.month, d.day, hour, rng.randint(0,59))
            cust = rng.choice(REGULARS) if rng.random() < 0.5 else rng.choice(CUSTOMERS)
            cust.order_count += 1
            cust.total_spent = round(cust.total_spent + revenue, 2)
            cust.loyalty_points += int(revenue)  # 1 pt per $
            orders.append(Order(f"ord_{oid:05d}", ts, channel, cust.id, lines,
                                deal.id if deal else None, revenue, fc, comm, net))
            oid += 1
            day_total += revenue
    orders.sort(key=lambda o: o.ts)
    return orders

ORDERS = generate_orders()

# ---------------------------------------------------------------------------
# 7. INVENTORY DEPLETION + BIWEEKLY RESTOCK  (well-stocked start)
# ---------------------------------------------------------------------------
def simulate_inventory():
    """Deplete ingredients as orders come in; restock every ~14 days.
    Returns the final stock state (with low-stock flags)."""
    # reset to starting stock
    for ing in INGREDIENTS.values():
        ing.stock = ing.restock_to
    last_restock = START
    for o in ORDERS:
        # biweekly restock
        if (o.ts.date() - last_restock).days >= 14:
            for ing in INGREDIENTS.values():
                ing.stock = ing.restock_to
            last_restock = o.ts.date()
        for l in o.lines:
            for iid, qty in MENU_BY_ID[l.item_id].recipe.items():
                INGREDIENTS[iid].stock -= qty * l.qty
    return INGREDIENTS

def inventory_status():
    simulate_inventory()
    out = []
    for ing in INGREDIENTS.values():
        status = "out" if ing.stock <= 0 else ("low" if ing.stock <= ing.reorder_point else "ok")
        out.append((ing.name, round(ing.stock, 1), ing.reorder_point, status,
                    round(ing.stock * ing.unit_cost, 2)))
    return out

# ---------------------------------------------------------------------------
# SANITY SUMMARY
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    rev = sum(o.revenue for o in ORDERS)
    fc  = sum(o.food_cost for o in ORDERS)
    comm= sum(o.commission_paid for o in ORDERS)
    net = sum(o.net_profit for o in ORDERS)
    print(f"Menu items: {len(MENU)}  |  Ingredients: {len(INGREDIENTS)}  |  Customers: {len(CUSTOMERS)}")
    print(f"Orders over {DAYS} days: {len(ORDERS)}  |  Avg order: ${rev/len(ORDERS):.2f}")
    print(f"Revenue ${rev:,.0f}  |  Food cost ${fc:,.0f}  |  Commission ${comm:,.0f}  |  Net ${net:,.0f}")
    print(f"Net margin: {100*net/rev:.1f}%")

    # daily revenue check vs targets
    from collections import defaultdict
    by_day = defaultdict(float)
    for o in ORDERS:
        by_day[o.ts.date()] += o.revenue
    wk = [v for d,v in by_day.items() if d.weekday() < 4]
    we = [v for d,v in by_day.items() if d.weekday() >= 4]
    print(f"Weekday avg/day ${sum(wk)/len(wk):.0f} (target 600-700)  |  "
          f"Weekend avg/day ${sum(we)/len(we):.0f} (target 1100-1200)")

    # channel profit (the commission story)
    from collections import defaultdict as dd
    cnet = dd(float); crev = dd(float)
    for o in ORDERS:
        crev[o.channel]+=o.revenue; cnet[o.channel]+=o.net_profit
    print("\nChannel        revenue    net    net%")
    for cid in CHANNEL_IDS:
        r=crev[cid]; n=cnet[cid]
        print(f"  {CHANNELS[cid].name:16} ${r:6,.0f}  ${n:6,.0f}   {100*n/r:4.1f}%")

    # deal popularity
    dd2 = dd(int)
    for o in ORDERS:
        if o.deal_id: dd2[o.deal_id]+=1
    print("\nDeal usage:")
    for did,c in sorted(dd2.items(), key=lambda x:-x[1]):
        print(f"  {DEALS[did].name:32} {c}")

    # low stock
    print("\nLow/out ingredients at end:")
    for name,stock,rp,status,val in inventory_status():
        if status!="ok": print(f"  [{status.upper():3}] {name:24} {stock} (reorder {rp})")