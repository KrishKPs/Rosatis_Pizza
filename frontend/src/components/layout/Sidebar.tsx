import { NavLink } from "react-router-dom";
import { FourStarRule } from "./FourStarRule";
import { useFilters } from "../../context/FiltersContext";
import { api } from "../../api/client";

// `short` is what fits in the phone tab bar; `label` is the desktop rail.
const NAV = [
  { to: "/", label: "Sales & Analytics", short: "Sales", icon: "◱" },
  { to: "/deals", label: "Deal Optimizer", short: "Deals", icon: "◈" },
  { to: "/inventory", label: "Inventory", short: "Stock", icon: "▤" },
  { to: "/menu", label: "Menu & Pricing", short: "Menu", icon: "▥" },
  { to: "/orders", label: "Orders & Channels", short: "Orders", icon: "◷" },
  { to: "/customers", label: "Customers & Loyalty", short: "People", icon: "◉" },
];

export function Sidebar() {
  const { meta, bumpRefresh } = useFilters();

  const handleReset = async () => {
    if (!confirm("Revert every edited cost, price, and deal assumption back to the seeded defaults?")) return;
    await api.resetOverrides();
    bumpRefresh();
  };

  return (
    // Phone/tablet: a fixed tab bar pinned under the content (order-last).
    // Desktop (lg+): the original vertical rail down the left.
    <aside
      className="order-last flex w-full shrink-0 border-t border-border bg-surface-2 px-1 pb-[env(safe-area-inset-bottom)]
                 lg:order-none lg:h-dvh lg:w-60 lg:flex-col lg:justify-between lg:border-t-0 lg:border-r lg:px-4 lg:py-5 lg:pb-5"
    >
      {/* `contents` dissolves this wrapper on phones so <nav> is a direct flex
          child of the bar; on desktop it groups brand + nav above the footer. */}
      <div className="contents lg:block">
        <div className="hidden px-1 lg:block">
          <div className="font-mono text-[15px] font-semibold tracking-tight text-text-primary">
            Rosati&rsquo;s Ops
          </div>
          <div className="mt-2 mb-4">
            <FourStarRule />
          </div>
        </div>

        <nav className="flex w-full flex-row justify-around lg:flex-col lg:gap-0.5">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex min-w-0 flex-1 flex-col items-center gap-1 rounded-lg px-1 py-2 font-mono text-[10px] transition-colors
                 lg:w-full lg:flex-none lg:flex-row lg:gap-2.5 lg:px-3 lg:py-2 lg:text-[13px] ${
                   isActive
                     ? "text-accent lg:bg-accent/[0.14]"
                     : "text-text-tertiary lg:text-text-secondary lg:hover:bg-surface-3 lg:hover:text-text-primary"
                 }`
              }
            >
              <span className="text-[15px] leading-none lg:w-4 lg:text-center lg:text-[13px]">{item.icon}</span>
              <span className="lg:hidden">{item.short}</span>
              <span className="hidden lg:inline">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="hidden px-1 lg:block">
        <button
          onClick={handleReset}
          className="mb-4 font-mono text-[11.5px] text-text-tertiary underline decoration-dotted underline-offset-2 hover:text-text-secondary"
        >
          Reset all edited costs
        </button>
        <div className="border-t border-border pt-3 text-[11.5px] leading-relaxed text-text-tertiary">
          {meta?.store_address ?? "6615 Falls of Neuse Rd, Suite 101, Raleigh, NC"}
          <br />
          Daily 10:30am–10pm
        </div>
      </div>
    </aside>
  );
}
