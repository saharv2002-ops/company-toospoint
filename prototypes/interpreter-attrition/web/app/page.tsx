"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { InterpreterTable } from "@/components/interpreter-table";
import { InterventionDialog } from "@/components/intervention-dialog";
import { KpiCard } from "@/components/kpi-card";
import { dashboardSummary } from "@/lib/api";
import type { InterpreterListItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function Home() {
  const [selected, setSelected] = useState<InterpreterListItem | null>(null);

  const summary = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: dashboardSummary,
  });

  return (
    <main className="mx-auto max-w-[1400px] px-6 py-8 md:px-10">
      {/* Header */}
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-neutral-500">
            At-risk interpreters, sorted by composite churn score.
          </p>
        </div>
        {summary.data?.as_of && (
          <span className="rounded-md border border-neutral-200 bg-white px-3 py-1.5 text-xs font-medium text-neutral-600">
            As of {formatDate(summary.data.as_of)}
          </span>
        )}
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
