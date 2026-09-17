"""
seed.py — the single seeded data foundation for Rosati's Ops (Raleigh).

Everything the app shows is generated here, reproducibly (fixed seed). Real menu
items and prices from the Raleigh store; gaps filled with realistic values and
marked FILLED. Ingredient unit costs are defaults — EDITABLE at runtime via the
store layer (see app/data/store.py), never here.

This module only builds the RAW seed: menu, ingredients, recipes, channels,
deals, customers, and orders. It does not compute food cost, margin, commission
or net profit for orders — those are DERIVED, live, from current (possibly
edited) costs by app/logic/profit.py. That's what makes editing a cost re-flow
every downstream number instead of baking stale numbers into history.

Run `python3 -m app.data.seed` from backend/ to print a sanity summary using
today's default costs.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

SEED = 1964  # Rosati's founding year; fixed so the demo is identical every run

REAL = "real"      # price/fact taken from the live Raleigh menu
FILLED = "filled"  # realistic default where the real number wasn't published

# ---------------------------------------------------------------------------
# 1. INGREDIENTS  (raw + prepped stock) — unit_cost is a starting default,
#    EDITABLE at runtime (see store.py). stock/reorder are simulation inputs.
# ---------------------------------------------------------------------------
@dataclass
class Ingredient:
    id: str
    name: str
    unit: str
    unit_cost: float
    reorder_point: float
    restock_to: float
    # "food" = recipe-tracked ingredient, "packaging" = recipe-tracked box/container,
    # "supply" = never appears in a recipe — counted-by-hand only (napkins, bags, gloves,
    # etc). See app/logic/manual_count.py for how kind changes what "on hand" means.
    kind: str = "food"


def build_ingredients() -> dict[str, Ingredient]:
    rows = [
        ("dough",     "Dough (per oz)",         "oz",   0.04, 2500, 9000),
        ("mozz",      "Mozzarella (per oz)",    "oz",   0.28, 2000, 7000),
        ("sauce",     "Pizza sauce (per oz)",   "oz",   0.06, 1500, 6000),
        ("pepperoni", "Pepperoni (per oz)",     "oz",   0.35,  500, 1800),
        ("sausage",   "Italian sausage (oz)",   "oz",   0.30,  450, 1600),
        ("beef",      "Italian beef (oz)",      "oz",   0.38,  250,  900),
        ("veggies",   "Veggie mix (per oz)",    "oz",   0.10,  500, 2000),
        ("pineapple", "Pineapple/ham (oz)",     "oz",   0.16,  200,  700),
        ("wings",     "Jumbo wings (each)",     "each", 0.42,  400, 1400),
        ("pasta",     "Pasta (per oz)",         "oz",   0.05,  600, 2400),
        ("alfredo",   "Alfredo sauce (oz)",     "oz",   0.09,  250,  900),
        ("chicken",   "Grilled chicken (oz)",   "oz",   0.34,  250,  900),
        ("marinara",  "Marinara (per oz)",      "oz",   0.05,  300, 1200),
        ("meatball",  "Meatballs (each)",       "each", 0.55,  150,  500),
        ("subroll",   "Sub roll (each)",        "each", 0.45,  150,  500),
        ("lettuce",   "Lettuce/salad mix (oz)", "oz",   0.07,  400, 1500),
        ("cheese_bl", "Cheese blend (oz)",      "oz",   0.26,  300, 1000),
        ("gfcrust",   "Gluten-free crust (ea)", "each", 1.80,   60,  200),
        ("soda2l",    "Soda 2L (each)",         "each", 1.10,  120,  400),
        ("can",       "Canned soda (each)",     "each", 0.35,  200,  800),
        ("dessert",   "Dessert unit (each)",    "each", 1.20,   90,  300),
    ]
    out = {r[0]: Ingredient(*r) for r in rows}
    # Pizza boxes — one SKU per size, so a manual count can literally match the
    # stack of flattened boxes behind the register (was a single generic "box").
    box_rows = [
        ("box_10", '10" pizza box',        "each", 0.28,  60,  220),
        ("box_12", '12" pizza box',        "each", 0.32, 220,  800),
        ("box_14", '14" pizza box',        "each", 0.38, 160,  600),
        ("box_16", '16" pizza box',        "each", 0.42, 140,  500),
        ("box_18", '18" pizza box',        "each", 0.48, 220,  800),
        ("box_calzone", "Calzone box",     "each", 0.30,  30,  120),
    ]
    for bid, name, unit, cost, rp, rt in box_rows:
        out[bid] = Ingredient(bid, name, unit, cost, rp, rt, kind="packaging")
    return out


def build_supplies() -> dict[str, Ingredient]:
    """Front-of-house/packaging supplies that never appear in a recipe, so order
    history can't tell us how many are left — the whole reason the manual count
    sheet (CLAUDE.md §7.3, "manual inventory check") exists. reorder_point /
    restock_to still apply; they're just compared against a hand count instead
    of a computed depletion."""
    rows = [
        ("napkins",       "Napkins (pack of 500)",         "pack",   3.50,  15,  60),
        ("carryout_bag",  "Carryout bags (each)",          "each",   0.12, 150, 600),
        ("utensil_kit",   "Plastic utensil kits (each)",   "each",   0.08, 100, 400),
        ("dip_cup",       "Dipping sauce cups (each)",     "each",   0.03, 200, 800),
        ("parm_packet",   "Parmesan/pepper packets (each)","each",   0.05, 150, 600),
        ("foil",          "Foil sheets (roll)",            "roll",   8.00,   2,   8),
        ("gloves",        "Food-service gloves (box)",     "box",    6.50,   4,  15),
        ("receipt_paper", "Receipt paper rolls (each)",    "each",   1.20,   8,  30),
        ("sanitizer",     "Sanitizer/degreaser (bottle)",  "bottle", 5.50,   3,  10),
    ]
    return {r[0]: Ingredient(*r, kind="supply") for r in rows}


# ---------------------------------------------------------------------------
# 2. MENU — real prices where found (REAL), realistic fills (FILLED).
#    food_cost is DERIVED from the recipe + ingredient unit costs (never typed
#    by hand) so recipe + ingredient cost are the single source of truth for
#    both item margin and inventory depletion.
# ---------------------------------------------------------------------------
@dataclass
class MenuItem:
    id: str
    name: str
    category: str
    price: float
    price_src: str
    recipe: dict[str, float]


PIZZA_BASE = {  # diameter(in): (dough_oz, mozz_oz, sauce_oz)
    10: (10, 6, 4), 12: (14, 8, 5), 14: (20, 11, 7), 16: (26, 14, 9), 18: (32, 18, 11),
}


def pizza_recipe(diam, toppings: dict[str, float] | None = None):
    d, m, s = PIZZA_BASE[diam]
    r = {"dough": d, "mozz": m, "sauce": s, f"box_{diam}": 1}
    if toppings:
        for k, v in toppings.items():
            r[k] = r.get(k, 0) + v
    return r


def build_menu() -> list[MenuItem]:
    menu: list[MenuItem] = []

    def add_pizza(pid, name, cat, price, src, diam, toppings=None):
        menu.append(MenuItem(pid, name, cat, price, src, pizza_recipe(diam, toppings)))

    BYO_PRICE = {12: 15.99, 14: 18.99, 16: 20.99, 18: 22.99}  # REAL (thin)
    DEEP_PRICE = {10: 17.99, 12: 20.49, 14: 21.99, 16: 24.49, 18: 27.49}  # 10 & 14 REAL
    for diam, base in BYO_PRICE.items():
        add_pizza(f"byo_thin_{diam}", f'{diam}" Build-Your-Own — Thin Crust', "Pizza", base, REAL, diam)
        add_pizza(f"byo_deep_{diam}", f'{diam}" Build-Your-Own — Deep Dish', "Pizza",
                  round(base + 2.00, 2), FILLED, diam, {"mozz": 4})
        add_pizza(f"byo_dbl_{diam}", f'{diam}" Build-Your-Own — Double Dough', "Pizza",
                  round(base + 3.00, 2), FILLED, diam, {"dough": PIZZA_BASE[diam][0] * 0.5})
    for diam, price in DEEP_PRICE.items():
        src = REAL if diam in (10, 14) else FILLED
        add_pizza(f"chi_{diam}", f'{diam}" Chicago Style', "Pizza", price, src, diam, {"mozz": 4, "sauce": 2})

    add_pizza("spec_monster_18", '18" Rosati\'s Monster', "Pizza", 34.99, REAL, 18,
              {"pepperoni": 4, "sausage": 4, "beef": 3, "veggies": 3})
    add_pizza("spec_monster_14", '14" Rosati\'s Monster', "Pizza", 28.99, REAL, 14,
              {"pepperoni": 3, "sausage": 3, "beef": 2, "veggies": 2})
    add_pizza("spec_monster_12", '12" Rosati\'s Monster', "Pizza", 25.99, REAL, 12,
              {"pepperoni": 2, "sausage": 2, "beef": 2, "veggies": 2})
    add_pizza("spec_meat_18", '18" Meat Mania', "Pizza", 31.99, REAL, 18,
              {"pepperoni": 4, "sausage": 4, "beef": 3})
    add_pizza("spec_four_16", '16" Fabulous Four', "Pizza", 27.99, REAL, 16,
              {"pepperoni": 3, "sausage": 3, "veggies": 2})
    add_pizza("spec_veg_16", '16" Veggie', "Pizza", 25.99, REAL, 16, {"veggies": 5})
    add_pizza("spec_combo_14", '14" Classic Combo', "Pizza", 25.99, REAL, 14,
              {"pepperoni": 3, "sausage": 3})
    add_pizza("spec_combo_12", '12" Classic Combo', "Pizza", 20.99, REAL, 12,
              {"pepperoni": 2, "sausage": 2})
    add_pizza("spec_haw_12", '12" Hawaiian', "Pizza", 19.99, REAL, 12, {"pineapple": 3})
    add_pizza("spec_white_12", '12" White', "Pizza", 19.99, REAL, 12, {"mozz": 4})
    add_pizza("gf_10", '10" Gluten Free', "Pizza", 12.99, REAL, 10, {"gfcrust": 1})

    menu += [
        MenuItem("wings_12", "12 Jumbo Wings", "Wings", 18.99, REAL, {"wings": 12}),
        MenuItem("wings_18", "18 Jumbo Wings", "Wings", 26.99, FILLED, {"wings": 18}),
        MenuItem("wings_6", "6 Jumbo Wings", "Wings", 10.99, FILLED, {"wings": 6}),
        MenuItem("wings_bl", "Boneless Wings (10)", "Wings", 11.99, FILLED, {"chicken": 8}),
    ]
    menu += [
        MenuItem("pasta_alfredo", "Fettuccine Alfredo w/ Grilled Chicken", "Pasta", 14.49, REAL,
                 {"pasta": 8, "alfredo": 5, "chicken": 5}),
        MenuItem("pasta_parm", "Chicken Parmigiana", "Pasta", 14.49, REAL,
                 {"pasta": 8, "marinara": 5, "chicken": 5, "mozz": 3}),
        MenuItem("pasta_penne", "Three Cheese Baked Penne", "Pasta", 15.49, REAL,
                 {"pasta": 9, "marinara": 5, "cheese_bl": 4}),
        MenuItem("pasta_spag", "Spaghetti & Meatball", "Pasta", 14.49, REAL,
                 {"pasta": 8, "marinara": 5, "meatball": 3}),
        MenuItem("pasta_byo", "Build-Your-Own Pasta", "Pasta", 14.49, REAL,
                 {"pasta": 8, "marinara": 5}),
    ]
    menu += [
        MenuItem("sand_beef", "Italian Beef Sandwich", "Sandwiches", 10.99, REAL,
                 {"subroll": 1, "beef": 6}),
        MenuItem("sand_sausage", "Italian Sausage Sandwich", "Sandwiches", 9.99, REAL,
                 {"subroll": 1, "sausage": 5}),
        MenuItem("sand_meatball", "Meatball Sandwich", "Sandwiches", 10.49, FILLED,
                 {"subroll": 1, "meatball": 3, "marinara": 3}),
    ]
    menu += [
        MenuItem("salad_garden", "Garden Salad", "Salad", 9.99, REAL, {"lettuce": 8, "veggies": 3}),
        MenuItem("salad_caesar", "Caesar Salad", "Salad", 9.49, FILLED, {"lettuce": 8, "cheese_bl": 1}),
        MenuItem("salad_chicken", "Chicken Caesar Salad", "Salad", 12.49, FILLED,
                 {"lettuce": 8, "chicken": 5, "cheese_bl": 1}),
    ]
    menu += [
        MenuItem("calzone", "Calzone", "Calzone", 12.99, REAL, {"dough": 16, "mozz": 8, "sauce": 3, "box_calzone": 1}),
    ]
    menu += [
        MenuItem("app_bread", "Garlic Bread", "Appetizers", 6.99, FILLED, {"dough": 8, "mozz": 3}),
        MenuItem("app_cheese", "Cheese Bread", "Appetizers", 8.49, FILLED, {"dough": 10, "mozz": 6}),
        MenuItem("app_sticks", "Mozzarella Sticks", "Appetizers", 8.99, FILLED, {"cheese_bl": 6}),
    ]
    menu += [
        MenuItem("des_cannoli", "Cannoli", "Desserts", 5.99, FILLED, {"dessert": 1}),
        MenuItem("des_brownie", "Chocolate Brownie", "Desserts", 5.49, FILLED, {"dessert": 1}),
    ]
    menu += [
        MenuItem("bev_2l", "2-Liter Soda", "Beverages", 3.99, FILLED, {"soda2l": 1}),
        MenuItem("bev_can", "Canned Soda", "Beverages", 1.99, FILLED, {"can": 1}),
    ]
    return menu


CATEGORIES = ["Pizza", "Sandwiches", "Pasta", "Salad", "Wings", "Appetizers",
              "Calzone", "Desserts", "Beverages"]

# ---------------------------------------------------------------------------
# 3. CHANNELS — commission is a starting default, EDITABLE at runtime.
# ---------------------------------------------------------------------------
@dataclass
class Channel:
    id: str
    name: str
    commission: float


def build_channels() -> dict[str, Channel]:
    rows = [
        ("dinein",   "Dine-In",            0.00),
        ("carryout", "Carryout",           0.00),
        ("delivery", "In-House Delivery",  0.00),
        ("doordash", "DoorDash",           0.25),
        ("ubereats", "Uber Eats",          0.25),
        ("grubhub",  "Grubhub",            0.20),
    ]
    return {r[0]: Channel(*r) for r in rows}


# ---------------------------------------------------------------------------
# 4. DEALS — the 6 real ones. incremental_fraction & attach_effect are MODELED
#    assumptions, EDITABLE at runtime. popularity_weight only shapes generation.
# ---------------------------------------------------------------------------
@dataclass
class Deal:
    id: str
    name: str
    code: str
    type: str  # percent | free_item | bogo | bundle
    popularity_weight: float
    incremental_fraction: float
    attach_effect: float
    availability: str  # 'daily' or a weekday name
    params: dict = field(default_factory=dict)


def build_deals() -> dict[str, Deal]:
    rows = [
        Deal("bogo", "BOGO — Buy 1 Pizza Get 1 Free", "BOGO", "bogo", 0.34, 0.35, 0.30, "daily",
             {"note": "second pizza free, equal or lesser value"}),
        Deal("family", "Family Deal", "FAMILY", "bundle", 0.22, 0.55, 0.60, "daily",
             {"price": 58.99, "contents": 'two 18" 1-topping + 12 wings'}),
        Deal("pizzanight", "Pizza Night", "PIZZANIGHT", "bundle", 0.16, 0.50, 0.35, "daily",
             {"price": 38.99, "contents": 'two 18" 1-topping pizzas'}),
        Deal("tenoff", "10% Off $20+", "10OFF", "percent", 0.14, 0.40, 0.20, "daily",
             {"percent": 0.10, "min_subtotal": 20}),
        Deal("free12", 'Free 12" with 18"', "FREE12", "free_item", 0.09, 0.45, 0.40, "daily",
             {"free_item": "byo_thin_12", "requires_18": True}),
        Deal("wednesday", "Wednesday 2 Pastas $21", "WEDNESDAY", "bundle", 0.05, 0.50, 0.30, "Wednesday",
             {"price": 21.00, "contents": "any 2 pastas"}),
    ]
    return {d.id: d for d in rows}


# ---------------------------------------------------------------------------
# 5. CUSTOMERS
# ---------------------------------------------------------------------------
FIRST_NAMES = ["James", "Maria", "David", "Linda", "Robert", "Patricia", "John", "Jennifer",
    "Michael", "Elizabeth", "Chris", "Susan", "Tony", "Angela", "Mark", "Nancy", "Paul", "Karen",
    "Steve", "Lisa", "Kevin", "Donna", "Brian", "Sandra", "Jason", "Amy", "Eric", "Rachel"]
LAST_NAMES = ["Smith", "Johnson", "Rossi", "Brown", "Davis", "Miller", "Wilson", "Moore",
    "Taylor", "Anderson", "Romano", "Ricci", "Nguyen", "Patel", "Garcia", "Martin", "Lee", "Clark"]


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


N_CUSTOMERS = 55
START = date(2026, 8, 10)  # a Monday; 4 weeks of history
DAYS = 28


# ---------------------------------------------------------------------------
# 6. ORDERS — a few weeks, realistic day/time shape. Orders only carry facts
#    determined AT THE TIME (what was ordered, on what channel, what deal, and
#    the revenue actually charged). Food cost / commission / net profit are
#    NOT stored — they are derived live from current costs by logic/profit.py,
#    so an edited cost re-flows every order retroactively. Single source of
#    truth per CLAUDE.md §8.
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


def _price_basket(lines, menu_by_id):
    return round(sum(menu_by_id[l.item_id].price * l.qty for l in lines), 2)


def _apply_deal(lines, deal, menu_by_id):
    subtotal = _price_basket(lines, menu_by_id)
    if deal.type == "percent" and subtotal >= deal.params.get("min_subtotal", 0):
        return -round(subtotal * deal.params["percent"], 2)
    if deal.type == "bogo":
        pizza_prices = sorted([menu_by_id[l.item_id].price for l in lines
                               if menu_by_id[l.item_id].category == "Pizza"])
        if len(pizza_prices) >= 2:
            return -pizza_prices[0]
        return 0.0
    if deal.type == "free_item":
        has18 = any('18"' in menu_by_id[l.item_id].name for l in lines)
        if has18:
            return -menu_by_id[deal.params["free_item"]].price
        return 0.0
    if deal.type == "bundle":
        return round(deal.params["price"] - subtotal, 2)
    return 0.0


def generate_dataset():
    """Build the whole deterministic seed: menu, ingredients, channels, deals,
    customers, orders. Pure function of SEED — call once and cache."""
    rng = random.Random(SEED)
    ingredients = {**build_ingredients(), **build_supplies()}
    menu = build_menu()
    menu_by_id = {m.id: m for m in menu}
    channels = build_channels()
    channel_ids = list(channels)
    deals = build_deals()

    customers: list[Customer] = []
    for i in range(N_CUSTOMERS):
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        fo = START + timedelta(days=rng.randint(0, DAYS - 1))
        customers.append(Customer(f"cust_{i:03d}", name, fo))
    regulars = customers[:18]

    pizzas = [m.id for m in menu if m.category == "Pizza"]
    sides = [m.id for m in menu if m.category in ("Wings", "Appetizers", "Salad")]
    drinks = [m.id for m in menu if m.category == "Beverages"]
    pastas = [m.id for m in menu if m.category == "Pasta"]
    desserts = [m.id for m in menu if m.category == "Desserts"]

    def weighted_deal(is_wed: bool):
        pool = [d for d in deals.values() if d.availability == "daily" or (is_wed and d.availability == "Wednesday")]
        return rng.choices(pool, weights=[d.popularity_weight for d in pool])[0]

    def build_basket(weekend: bool):
        lines = []
        n_pizza = rng.choice([1, 1, 2] if not weekend else [1, 2, 2, 3])
        for _ in range(n_pizza):
            lines.append(OrderLine(rng.choice(pizzas), 1))
        if rng.random() < (0.75 if weekend else 0.45):
            lines.append(OrderLine(rng.choice(sides), 1))
        if rng.random() < (0.7 if weekend else 0.5):
            lines.append(OrderLine(rng.choice(drinks), rng.choice([1, 1, 2])))
        if weekend and rng.random() < 0.3:
            lines.append(OrderLine(rng.choice(desserts), 1))
        if rng.random() < 0.15:
            lines.append(OrderLine(rng.choice(pastas), 1))
        return lines

    orders: list[Order] = []
    oid = 0
    for day_i in range(DAYS):
        d = START + timedelta(days=day_i)
        weekend = d.weekday() >= 4
        is_wed = d.weekday() == 2
        target = rng.uniform(1100, 1200) if weekend else rng.uniform(600, 700)
        day_total = 0.0
        guard = 0
        while day_total < target and guard < 200:
            guard += 1
            lines = build_basket(weekend)
            revenue = _price_basket(lines, menu_by_id)
            deal = None
            if rng.random() < 0.55:
                deal = weighted_deal(is_wed)
                revenue = round(revenue + _apply_deal(lines, deal, menu_by_id), 2)
            if revenue <= 0:
                continue
            channel = rng.choice(channel_ids)
            hour = rng.choice([11, 12, 12, 13, 17, 18, 18, 19, 19, 20]) if weekend \
                else rng.choice([11, 12, 13, 17, 18, 19, 20])
            ts = datetime(d.year, d.month, d.day, hour, rng.randint(0, 59))
            cust = rng.choice(regulars) if rng.random() < 0.5 else rng.choice(customers)
            cust.order_count += 1
            cust.total_spent = round(cust.total_spent + revenue, 2)
            cust.loyalty_points += int(revenue)
            orders.append(Order(f"ord_{oid:05d}", ts, channel, cust.id, lines,
                                 deal.id if deal else None, revenue))
            oid += 1
            day_total += revenue
    orders.sort(key=lambda o: o.ts)

    return {
        "ingredients": ingredients,
        "menu": menu,
        "menu_by_id": menu_by_id,
        "channels": channels,
        "deals": deals,
        "customers": customers,
        "orders": orders,
    }


if __name__ == "__main__":
    ds = generate_dataset()
    print(f"Menu items: {len(ds['menu'])}  |  Ingredients: {len(ds['ingredients'])}  "
          f"|  Customers: {len(ds['customers'])}  |  Orders: {len(ds['orders'])}")
    rev = sum(o.revenue for o in ds["orders"])
    print(f"Total revenue over {DAYS} days: ${rev:,.0f}  |  Avg order: ${rev/len(ds['orders']):.2f}")
