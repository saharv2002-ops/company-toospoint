"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import { useState } from "react";
import { InterpreterTable } from "@/components/interpreter-table";
import { InterventionDialog } from "@/components/intervention-dialog";
import { KpiCard } from "@/components/kpi-card";
import { Button } from "@/components/ui/button";
import { backfillScores, dashboardSummary, recomputeScores } from "@/lib/api";
import type { InterpreterListItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const IS_DEV_UI = process.env.NEXT_PUBLIC_SHOW_DEV_UI !== "false";

export default function Home() {
  const qc = useQueryClient();
  const [selected, setSelected] = useState<InterpreterListItem | null>(null);

  const summary = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: dashboardSummary,
  });

  const recompute = useMutation({
    mutationFn: async () => {
      await recomputeScores();
      await backfillScores(14);
    },
    onSuccess: () => {
      qc.invalidateQueries();
    },
  });

  return (
    <main className="mx-auto max-w-[1400px] px-6 py-8 md:px-10">
      {/* Header */}
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-[10px] font-medium uppercase tracking-widest text-neutral-500">
            Interpreter attrition · early warning
          </div>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-neutral-900">
            ChurnScope
          </h1>
        </div>
        <div className="flex items-center gap-3">
          {summary.data?.as_of && (
            <span className="rounded-md border border-neutral-200 bg-white px-3 py-1.5 text-xs font-medium text-neutral-600">
              As of {formatDate(summary.data.as_of)}
            </span>
          )}
          {IS_DEV_UI && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => recompute.mutate()}
              disabled={recompute.isPending}
            >
              <RefreshCcw className="h-3.5 w-3.5" />
              {recompute.isPending ? "Recomputing…" : "Recompute"}
            </Button>
          )}
        </div>
      </div>

      {/* KPI cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <KpiCard
          label="Red band"
          value={summary.data ? summary.data.band_counts.red.toLocaleString() : "—"}
          delta={summary.data?.week_over_week.red_delta}
          accent="red"
          hint="Intervene this week"
        />
        <KpiCard
          label="Yellow band"
          value={summary.data ? summary.data.band_counts.yellow.toLocaleString() : "—"}
          delta={summary.data?.week_over_week.yellow_delta}
          accent="yellow"
          hint="Watch closely"
        />
        <KpiCard
          label="Active roster"
          value={summary.data ? summary.data.total_active.toLocaleString() : "—"}
          hint="Interpreters marked active"
        />
      </div>

      {/* Risk table */}
      <InterpreterTable onLogIntervention={setSelected} />

      {/* Intervention dialog */}
      <InterventionDialog
        interpreterId={selected?.id ?? null}
        interpreterName={selected?.full_name}
        onClose={() => setSelected(null)}
      />
    </main>
  );
}
