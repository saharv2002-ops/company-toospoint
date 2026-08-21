import type { SignalReadout } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Progress } from "./ui/progress";

export function SignalBreakdown({ signals }: { signals: SignalReadout[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Signal breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-neutral-100">
          {signals.map((s) => (
            <div key={s.key} className="grid grid-cols-12 items-start gap-4 py-4 first:pt-0 last:pb-0">
              <div className="col-span-4 md:col-span-3">
                <div className="text-sm font-medium text-neutral-900">{s.name}</div>
                <div className="mt-0.5 font-mono text-[11px] uppercase tracking-widest text-neutral-500">
                  weight {s.weight}
                </div>
              </div>
              <div className="col-span-8 md:col-span-9">
                <div className="flex items-center gap-3">
                  <Progress value={s.score} className="flex-1" />
                  <span className="w-8 shrink-0 text-right text-sm font-semibold tabular-nums text-neutral-900">
                    {s.score}
                  </span>
                </div>
                <div className="mt-1.5 text-xs leading-relaxed text-neutral-600">
                  {s.why}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
