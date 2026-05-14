import { NavLink, useLocation } from "react-router-dom";
import {
  BarChart3,
  CandlestickChart,
  Link2,
  Grid3X3,
  Search,
  AlertTriangle,
  Settings,
  TrendingUp,
  Activity,
} from "lucide-react";

const navItems = [
  { to: "/", icon: BarChart3, label: "Dashboard" },
  { to: "/asset-explorer", icon: CandlestickChart, label: "Asset Explorer" },
  { to: "/similarity", icon: Link2, label: "Similarity Analysis" },
  { to: "/correlation", icon: Grid3X3, label: "Correlation Heatmap" },
  { to: "/patterns", icon: Search, label: "Pattern Detection" },
  { to: "/risk", icon: AlertTriangle, label: "Risk Dashboard" },
];

export default function AppSidebar() {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-16 flex-col border-r border-border bg-sidebar lg:w-56">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-border px-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
          <Activity className="h-5 w-5 text-primary" />
        </div>
        <span className="hidden text-sm font-bold tracking-wide text-foreground lg:block">
          Nex<span className="text-primary">Vest</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={`group flex items-center gap-3 rounded-md px-2 py-2.5 text-sm transition-colors ${
                isActive
                  ? "border-l-2 border-primary bg-sidebar-accent text-primary"
                  : "border-l-2 border-transparent text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              }`}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span className="hidden lg:block">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-border p-2">
        <NavLink
          to="/settings"
          className={`flex items-center gap-3 rounded-md px-2 py-2.5 text-sm transition-colors ${
            location.pathname === "/settings"
              ? "border-l-2 border-primary bg-sidebar-accent text-primary"
              : "border-l-2 border-transparent text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          }`}
        >
          <Settings className="h-4 w-4 shrink-0" />
          <span className="hidden lg:block">Settings</span>
        </NavLink>

        {/* Portfolio summary */}
        <div className="mt-3 hidden rounded-md border border-border bg-muted/50 p-2 lg:block">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <TrendingUp className="h-3 w-3 text-primary" />
            <span>Portfolio: 20 assets</span>
          </div>
          <div className="mt-1 text-xs font-mono text-foreground">+4.82% MTD</div>
        </div>

        {/* ETL Status */}
        <div className="mt-2 flex items-center gap-2 px-2 py-1">
          <span className="h-2 w-2 rounded-full bg-success animate-pulse-glow" />
          <span className="hidden text-xs text-muted-foreground lg:block">Data updated</span>
        </div>
      </div>
    </aside>
  );
}
