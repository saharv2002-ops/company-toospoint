"use client";

import { useQuery } from "@tanstack/react-query";
import { listInterventions } from "@/lib/api";
import type { InterventionAction } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

const ACTION_LABEL: Record<InterventionAction, string> = {
  coach_call: "Coach call",
  assign_mentor: "Assign mentor",
  schedule_flex: "Schedule flex",
  comp_bonus: "Comp bonus",
  no_action: "No action",
};

export function InterventionLog({ interpreterId }: { interpreterId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["interventions", { interpreter_id: interpreterId }],
    queryFn: () => listInterventions({ interpreter_id: interpreterId, limit: 50 }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Intervention log</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="py-4 text-sm text-neutral-500">Loading…</div>
        )}
        {data && data.items.length === 0 && (
          <div className="py-4 text-sm text-neutral-500">
            No interventions logged. Use “Log intervention” to record the next one.
          </div>
        )}
        {data && data.items.length > 0 && (
          <div className="divide-y divide-neutral-100">
            {data.items.map((iv) => (
              <div key={iv.id} className="flex items-start gap-4 py-3 first:pt-0 last:pb-0">
                <div className="w-32 shrink-0">
                  <Badge className="bg-neutral-100 text-neutral-700 ring-neutral-200">
                    {ACTION_LABEL[iv.action]}
                  </Badge>
                </div>
                <div className="flex-1 text-sm">
                  {iv.notes ? (
                    <div className="text-neutral-800">{iv.notes}</div>
                  ) : (
                    <div className="italic text-neutral-400">No notes</div>
                  )}
                  {iv.outcome && (
                    <div className="mt-0.5 text-xs text-neutral-500">
                      Outcome: {iv.outcome}
                    </div>
                  )}
                </div>
                <div className="w-24 shrink-0 text-right text-xs text-neutral-500">
                  {formatDate(iv.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
