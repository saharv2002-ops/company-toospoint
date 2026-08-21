"use client";

import { useQuery } from "@tanstack/react-query";
import { Line, LineChart, ResponsiveContainer, Tooltip, YAxis } from "recharts";
import { getTimeline } from "@/lib/api";
import type { TimelinePoint } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

interface Props {
  interpreterId: string;
  days?: number;
}

interface SignalMeta {
  key: keyof TimelinePoint;
  label: string;
}

const SIGNALS: SignalMeta[] = [
  { key: "signal_1_volume", label: "Volume" },
  { key: "signal_2_decline", label: "Decline rate" },
  { key: "signal_3_latency", label: "Latency" },
  { key: "signal_4_feedback", label: "Feedback" },
  { key: "signal_5_tenure", label: "Tenure" },
  { key: "signal_6_availability", label: "Availability" },
];

function SparkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-neutral-200 bg-white px-2 py-1.5 text-xs shadow-md">
      <div className="font-medium text-neutral-900">{payload[0].value}</div>
      <div className="text-[10px] text-neutral-500">{formatDate(label)}</div>
    </div>
  );
}

export function SparklineGrid({ interpreterId, days = 30 }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["timeline", interpreterId, days],
    queryFn: () => getTimeline(interpreterId, days),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Last {days} days — signal history</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="py-6 text-center text-sm text-neutral-500">Loading timeline…</div>
        )}
        {isError && (
          <div className="py-6 text-center text-sm text-red-700">
            Could not load timeline. Was <code>POST /api/scores/backfill</code> run?
          </div>
        )}
        {data && data.points.length === 0 && (
          <div className="py-6 text-center text-sm text-neutral-500">
            No historical scores yet. Run <code>POST /api/scores/backfill?days={days}</code> to
            populate.
          </div>
        )}
        {data && data.points.length > 0 && (
          <div className="grid grid-cols-2 gap-6 md:grid-cols-3">
            {SIGNALS.map((sig) => (
              <div key={sig.key}>
                <div className="mb-1 flex items-baseline justify-between">
                  <div className="text-xs font-medium text-neutral-700">{sig.label}</div>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-400">
                    {data.points[data.points.length - 1][sig.key]}
                  </div>
                </div>
                <div className="h-16">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={data.points}
                      margin={{ top: 4, right: 2, bottom: 2, left: 2 }}
                    >
                      <YAxis hide domain={[0, 100]} />
                      <Tooltip
                        content={<SparkTooltip />}
                        cursor={{ stroke: "#e5e5e5", strokeWidth: 1 }}
                      />
                      <Line
                        type="monotone"
                        dataKey={sig.key}
                        stroke="#0a0a0a"
                        strokeWidth={1.5}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
