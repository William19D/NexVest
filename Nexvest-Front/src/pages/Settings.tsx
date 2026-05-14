import { KeyRound, Calendar, ListPlus, Save, Activity } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-foreground">Settings</h1>

      {/* API Keys */}
      <div className="rounded-lg border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <KeyRound className="h-5 w-5 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">API Configuration</h2>
        </div>
        {["BVC API Key", "Alpha Vantage Key", "Yahoo Finance Token"].map((label) => (
          <div key={label}>
            <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">{label}</label>
            <input
              type="password"
              placeholder="••••••••••••••••"
              className="w-full rounded-md border border-border bg-muted px-3 py-2 text-sm font-mono text-foreground placeholder:text-muted-foreground/50"
            />
          </div>
        ))}
      </div>

      {/* Date Range */}
      <div className="rounded-lg border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Calendar className="h-5 w-5 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">Date Range Configuration</h2>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Start Date</label>
            <input type="date" defaultValue="2021-01-01" className="w-full rounded-md border border-border bg-muted px-3 py-2 text-sm font-mono text-foreground" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">End Date</label>
            <input type="date" defaultValue="2026-02-18" className="w-full rounded-md border border-border bg-muted px-3 py-2 text-sm font-mono text-foreground" />
          </div>
        </div>
      </div>

      {/* Asset List */}
      <div className="rounded-lg border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <ListPlus className="h-5 w-5 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">Asset List Management</h2>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Tracked Assets (comma-separated)</label>
          <textarea
            rows={3}
            defaultValue="ECOPETROL, ISA, GEB, PFBCOLOM, NUTRESA, GRUPOSURA, CEMARGOS, ETB, VOO, CSPX, QQQ, EEM, GLD, SLV, SPY, IWDA"
            className="w-full rounded-md border border-border bg-muted px-3 py-2 text-sm font-mono text-foreground resize-none"
          />
        </div>
      </div>

      <button className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors">
        <Save className="h-4 w-4" /> Save Settings
      </button>

      {/* Footer branding */}
      <div className="border-t border-border pt-6 mt-8 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
            <Activity className="h-3.5 w-3.5 text-primary" />
          </div>
          <span className="text-sm font-semibold text-foreground">
            Nex<span className="text-primary">Vest</span>
          </span>
        </div>
        <span className="text-xs font-mono text-muted-foreground">v1.0.0</span>
      </div>
    </div>
  );
}
