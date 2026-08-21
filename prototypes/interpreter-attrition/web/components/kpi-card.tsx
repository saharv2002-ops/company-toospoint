import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: number | string;
  delta?: number;
  accent?: "red" | "yellow" | "neutral";
  hint?: string;
}

const accentBar: Record<Required<KpiCardProps>["accent"], string> = {
  red: "bg-band-red",
  yellow: "bg-band-yellow",
  neutral: "bg-neutral-300",
};

const accentText: Record<Required<KpiCardProps>["accent"], string> = {
  red: "text-band-red",
  yellow: "text-yellow-700",
  neutral: "text-neutral-800",
};

export function KpiCard({ label, value, delta, accent = "neutral", hint }: KpiCardProps) {
  const positiveIsBad = accent !== "neutral"; // red / yellow bands: rising count = worse
  const trendIsBad =
    delta !== undefined && (positiveIsBad ? delta > 0 : delta < 0);
  const trendIsGood =
    delta !== undefined && (positiveIsBad ? delta < 0 : delta > 0);

  return (
    <Card className="relative overflow-hidden">
      <div className={cn("absolute inset-y-0 left-0 w-1", accentBar[accent])} />
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className={cn("text-4xl font-semibold tracking-tight", accentText[accent])}>
            {value}
          </div>
          {delta !== undefined && (
            <div
              className={cn(
                "flex items-center gap-1 text-xs font-medium",
                trendIsBad
                  ? "text-red-600"
                  : trendIsGood
                  ? "text-green-600"
                  : "text-neutral-500"
              )}
            >
              {delta > 0 ? (
                <ArrowUp className="h-3.5 w-3.5" />
              ) : delta < 0 ? (
                <ArrowDown className="h-3.5 w-3.5" />
              ) : (
                <Minus className="h-3.5 w-3.5" />
              )}
              <span>{delta > 0 ? `+${delta}` : delta} vs 7 d</span>
            </div>
          )}
        </div>
        {hint && <div className="mt-1 text-xs text-neutral-500">{hint}</div>}
      </CardContent>
    </Card>
  );
}
