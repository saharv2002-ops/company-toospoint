"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { RetentionChart } from "@/components/retention-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FieldLabel, Select } from "@/components/ui/input";
import { TBody, TD, TH, THead, TR, Table } from "@/components/ui/table";
import { listInterventions } from "@/lib/api";
import type { InterventionAction } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const ACTION_LABEL: Record<InterventionAction, string> = {
  coach_call: "Coach call",
  assign_mentor: "Assign mentor",
  schedule_flex: "Schedule flex",
  comp_bonus: "Comp bonus",
  no_action: "No action",
};

export default function InterventionsPage() {
  const [action, setAction] = useState<InterventionAction | "">("");
  const [outcome, setOutcome] = useState<string>("");
  const [sinceDays, setSinceDays] = useState<string>("30");

  const params = useMemo(
    () => ({
      action: action || undefined,
      outcome: outcome || undefined,
      since_days: sinceDays ? Number(sinceDays) : undefined,
      limit: 500,
    }),
    [action, outcome, sinceDays]
  );

  const { data, isLoading, isError } = useQuery({
    queryKey: ["interventions", params],
    queryFn: () => listInterventions(params),
  });

  const activeFilters = [action, outcome, sinceDays].filter(Boolean).length;

  return (
    <main className="mx-auto max-w-[1400px] px-6 py-8 md:px-10">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">
          Interventions
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Every intervention logged across the roster, plus the retention outcomes
          they lead to.
        </p>
      </div>

      <div className="mb-6">
        <RetentionChart items={data?.items ?? []} />
      </div>

      <div className="rounded-lg border border-neutral-200 bg-white shadow-sm">
        <div className="grid grid-cols-2 gap-4 border-b border-neutral-100 p-4 md:grid-cols-5">
          <div>
            <FieldLabel htmlFor="f-action">Action</FieldLabel>
            <Select
              id="f-action"
              value={action}
              onChange={(e) => setAction(e.target.value as InterventionAction | "")}
            >
              <option value="">All</option>
              {Object.entries(ACTION_LABEL).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <FieldLabel htmlFor="f-outcome">Outcome</FieldLabel>
            <Select
              id="f-outcome"
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
            >
              <option value="">All</option>
              <option value="retained">Retained</option>
              <option value="churned">Churned</option>
              <option value="pending">Pending</option>
            </Select>
          </div>
          <div>
            <FieldLabel htmlFor="f-since">Since (days)</FieldLabel>
            <Select
              id="f-since"
              value={sinceDays}
              onChange={(e) => setSinceDays(e.target.value)}
            >
              <option value="">All time</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
              <option value="365">Last year</option>
            </Select>
          </div>
          <div className="col-span-2 flex items-end justify-end">
            <Button
              variant="outline"
              onClick={() => {
                setAction("");
                setOutcome("");
                setSinceDays("");
              }}
              disabled={activeFilters === 0}
            >
              Reset filters
            </Button>
          </div>
        </div>

        {isLoading && (
          <div className="p-8 text-center text-sm text-neutral-500">Loading interventions…</div>
        )}
        {isError && (
          <div className="flex items-center gap-2 p-8 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4" />
            Could not load interventions.
          </div>
        )}
        {data && data.items.length === 0 && (
          <div className="p-8 text-center text-sm text-neutral-500">
            No interventions match these filters. Log one from any interpreter’s
            detail page.
          </div>
        )}
        {data && data.items.length > 0 && (
          <>
            <Table>
              <THead>
                <TR>
                  <TH className="w-[26%]">Interpreter</TH>
                  <TH className="w-[14%]">Action</TH>
                  <TH className="w-[34%]">Notes</TH>
                  <TH className="w-[12%]">Outcome</TH>
                  <TH className="w-[14%]">Logged</TH>
                </TR>
              </THead>
              <TBody>
                {data.items.map((iv) => (
                  <TR key={iv.id}>
                    <TD>
                      <Link
                        href={`/interpreters/${iv.interpreter_id}`}
                        className="group block"
                      >
                        <div className="font-medium text-neutral-900 group-hover:underline">
                          {iv.interpreter_name}
                        </div>
                        <div className="font-mono text-xs text-neutral-500">
                          {iv.interpreter_external_id}
                        </div>
                      </Link>
                    </TD>
                    <TD>
                      <Badge className="bg-neutral-100 text-neutral-700 ring-neutral-200">
                        {ACTION_LABEL[iv.action]}
                      </Badge>
                    </TD>
                    <TD>
                      {iv.notes ? (
                        <span className="text-neutral-700">{iv.notes}</span>
                      ) : (
                        <span className="italic text-neutral-400">—</span>
                      )}
                    </TD>
                    <TD>
                      {iv.outcome ? (
                        <span className="text-sm capitalize text-neutral-700">
                          {iv.outcome}
                        </span>
                      ) : (
                        <span className="text-sm text-neutral-400">pending</span>
                      )}
                    </TD>
                    <TD className="text-sm text-neutral-500">{formatDate(iv.created_at)}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
            <div className="border-t border-neutral-100 px-4 py-3 text-xs text-neutral-500">
              Showing {data.items.length} of {data.total.toLocaleString()} interventions
              {activeFilters > 0 && ` (${activeFilters} filter${activeFilters > 1 ? "s" : ""} applied)`}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
