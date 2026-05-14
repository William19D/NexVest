import { LucideIcon, BarChart3 } from "lucide-react";

interface ChartPlaceholderProps {
  label: string;
  height?: string;
  icon?: LucideIcon;
}

export default function ChartPlaceholder({ label, height = "h-64", icon: Icon = BarChart3 }: ChartPlaceholderProps) {
  return (
    <div className={`${height} flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30`}>
      <Icon className="mb-2 h-8 w-8 text-muted-foreground/50" />
      <span className="text-sm text-muted-foreground">{label}</span>
    </div>
  );
}
