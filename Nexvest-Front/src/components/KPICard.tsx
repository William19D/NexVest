import { ReactNode } from "react";

interface KPICardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  accent?: "teal" | "amber" | "default";
}

export default function KPICard({ label, value, icon, accent = "teal" }: KPICardProps) {
  const borderClass = accent === "teal" ? "border-l-primary" : accent === "amber" ? "border-l-accent" : "border-l-border";

  return (
    <div className={`rounded-lg border border-border bg-card p-4 border-l-4 ${borderClass}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground uppercase tracking-wider">{label}</span>
        <span className="text-muted-foreground">{icon}</span>
      </div>
      <div className="mt-2 text-xl font-semibold font-mono text-foreground">{value}</div>
    </div>
  );
}
