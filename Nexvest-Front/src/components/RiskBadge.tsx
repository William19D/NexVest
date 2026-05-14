import { RiskCategory } from "@/types/risk";

export default function RiskBadge({ category }: { category: RiskCategory }) {
  const styles = {
    Conservative: "bg-success/15 text-success border-success/30",
    Moderate: "bg-warning/15 text-warning border-warning/30",
    Aggressive: "bg-danger/15 text-danger border-danger/30",
  };

  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[category]}`}>
      {category}
    </span>
  );
}
