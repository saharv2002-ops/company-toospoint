"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { InterventionDialog } from "@/components/intervention-dialog";
import { InterventionLog } from "@/components/intervention-log";
import { SignalBreakdown } from "@/components/signal-breakdown";
import { SparklineGrid } from "@/components/sparkline-grid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getInterpreter } from "@/lib/api";
import { bandBadgeClass, formatDate } from "@/lib/utils";

export default function InterpreterDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["interpreter", id],
    queryFn: () => getInterpreter(id!),
    enabled: Boolean(id),
  });

  if (!id) return null;

  return (
    <main className="mx-auto max-w-[1400px] px-6 py-8 md:px-10">
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-1.5 text-xs font-medium uppercase tracking-widest text-neutral-500 hover:text-neutral-900"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to dashboard
      </Link>

      {isLoading && (
        <div className="rounded-lg border border-neutral-200 bg-white p-8 text-center text-sm text-neutral-500">
          Loading interpreter…
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-sm text-red-700">
          Failed to load interpreter.
          <div className="mt-2 font-mono text-xs">{String(error)}</div>
        </div>
      )}

      {data && (
        <>
          {/* Header */}
          <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-widest text-neutral-500">
                {data.external_id} · {data.status}
              </div>
              <h1 className="mt-1 text-3xl font-semibold tracking-tight text-neutral-900">
                {data.full_name}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {data.languages.map((l) => (
                  <Badge key={l} className="bg-neutral-100 text-neutral-700 ring-neutral-200">
                    {l}
                  </Badge>
                ))}
                <span className="text-xs text-neutral-500">
                  {(data.tenure_days / 30.44).toFixed(1)} mo tenure ·
                  hired {formatDate(data.hired_at)}
                  {data.home_timezone && ` · ${data.home_timezone}`}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-4">
              {data.latest_score && (
                <div className="text-right">
                  <div className="text-[10px] font-medium uppercase tracking-widest text-neutral-500">
                    Score · {formatDate(data.latest_score.as_of)}
                  </div>
                  <div className="mt-1 flex items-baseline justify-end gap-2">
                    <span className="text-4xl font-semibold tabular-nums text-neutral-900">
                      {data.latest_score.composite_score}
                    </span>
                    <Badge className={bandBadgeClass(data.latest_score.band)}>
                      {data.latest_score.band}
                    </Badge>
                  </div>
                </div>
              )}
              <Button onClick={() => setDialogOpen(true)}>Log intervention</Button>
            </div>
          </div>

          <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <SignalBreakdown signals={data.signals} />
            </div>
            <div>
              <InterventionLog interpreterId={data.id} />
            </div>
          </div>

          <div className="mb-6">
            <SparklineGrid interpreterId={data.id} days={30} />
          </div>

          {data.recent_intervention_count > 0 && (
            <div className="text-xs text-neutral-500">
              {data.recent_intervention_count} intervention
              {data.recent_intervention_count === 1 ? "" : "s"} logged in the last 30 days.
            </div>
          )}
        </>
      )}

      <InterventionDialog
        interpreterId={dialogOpen ? id : null}
        interpreterName={data?.full_name}
        onClose={() => setDialogOpen(false)}
      />
    </main>
  );
}
