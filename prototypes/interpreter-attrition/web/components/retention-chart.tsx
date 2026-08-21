"use client";

import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { InterventionAction, InterventionListItem } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

const ACTION_LABELS: Record<InterventionAction, string> = {
  coach_call: "Coach",
  assign_mentor: "Mentor",
  schedule_flex: "Flex",
  comp_bonus: "Bonus",
  no_action: "None",
};

const OUTCOME_COLORS = {
  retained: "#16a34a",   // band-green
  churned: "#dc2626",    // band-red
  pending: "#a3a3a3",    // neutral
};

type Row = {
  action: string;
  retained: number;
  churned: number;
  pending: number;
};

function aggregate(items: InterventionListItem[]): Row[] {
  const buckets: Record<string, Row> = {};
  for (const action of Object.keys(ACTION_LABELS) as InterventionAction[]) {
    buckets[action] = {
      action: ACTION_LABELS[action],
      retained: 0,
      churned: 0,
      pending: 0,
    };
  }
  for (const item of items) {
    const bucket = buckets[item.action];
    if (!bucket) continue;
    const outcome = (item.outcome ?? "pending").toLowerCase();
    if (outcome === "retained") bucket.retained += 1;
    else if (outcome === "churned") bucket.churned += 1;
    else bucket.pending += 1;
  }
  return Object.values(buckets);
}

export function RetentionChart({ items }: { items: InterventionListItem[] }) {
  const rows = aggregate(items);
  const hasAnything = rows.some((r) => r.retained + r.churned + r.pending > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Retention outcomes by intervention</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasAnything && (
          <div className="py-6 text-sm text-neutral-500">
            No interventions logged yet. Chart fills in as interpreters continue or
            churn over the next 30 days.
          </div>
        )}
        {hasAnything && (
          <>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
                  <CartesianGrid stroke="#f5f5f5" vertical={false} />
                  <XAxis
                    dataKey="action"
                    stroke="#a3a3a3"
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                  />
                  <YAxis
                    stroke="#a3a3a3"
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 6,
                      border: "1px solid #e5e5e5",
                      fontSize: 12,
                    }}
                    cursor={{ fill: "#fafafa" }}
                  />
                  <Legend
                    iconType="square"
                    wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
                  />
                  <Bar dataKey="retained" stackId="s" name="Retained">
                    <Cell fill={OUTCOME_COLORS.retained} />
                  </Bar>
                  <Bar dataKey="churned" stackId="s" name="Churned">
                    <Cell fill={OUTCOME_COLORS.churned} />
                  </Bar>
                  <Bar dataKey="pending" stackId="s" name="Pending">
                    <Cell fill={OUTCOME_COLORS.pending} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 text-xs text-neutral-500">
              Retention outcomes update as interpreters continue or churn over the
              next 30 days.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
