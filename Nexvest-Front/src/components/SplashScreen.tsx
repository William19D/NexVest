import { useState, useEffect } from "react";
import { Activity } from "lucide-react";

export default function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<"logo" | "text" | "fade">("logo");

  useEffect(() => {
    const t1 = setTimeout(() => setPhase("text"), 600);
    const t2 = setTimeout(() => setPhase("fade"), 1800);
    const t3 = setTimeout(onComplete, 2300);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [onComplete]);

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-background transition-opacity duration-500 ${
        phase === "fade" ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className={`flex items-center gap-3 transition-all duration-700 ${phase === "logo" ? "scale-90 opacity-0" : "scale-100 opacity-100"}`}>
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/15 glow-border">
          <Activity className="h-7 w-7 text-primary animate-pulse" />
        </div>
        <span className="text-3xl font-bold tracking-tight text-foreground">
          Nex<span className="text-primary">Vest</span>
        </span>
      </div>
      <p className={`mt-4 text-sm text-muted-foreground font-mono transition-all duration-500 delay-200 ${
        phase === "text" || phase === "fade" ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
      }`}>
        Quantitative Analysis Platform
      </p>
      <div className="mt-8 h-0.5 w-32 overflow-hidden rounded-full bg-border">
        <div className="h-full animate-pulse rounded-full bg-primary" style={{ width: "60%" }} />
      </div>
    </div>
  );
}
