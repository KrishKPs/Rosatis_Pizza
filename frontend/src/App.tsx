import { Route, Routes } from "react-router-dom";
import { Sidebar } from "./components/layout/Sidebar";
import { SalesPage } from "./pages/SalesPage";
import { DealsPage } from "./pages/DealsPage";
import { InventoryPage } from "./pages/InventoryPage";
import { MenuPage } from "./pages/MenuPage";
import { OrdersPage } from "./pages/OrdersPage";
import { CustomersPage } from "./pages/CustomersPage";

export default function App() {
  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-bg lg:flex-row">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<SalesPage />} />
          <Route path="/deals" element={<DealsPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/menu" element={<MenuPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/customers" element={<CustomersPage />} />
        </Routes>
      </main>
    </div>
  );
}
