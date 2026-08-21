"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useMemo, useState } from "react";
import { listInterpreters } from "@/lib/api";
import type { Band, InterpreterFilters, InterpreterListItem } from "@/lib/types";
import { bandBadgeClass, bandBorderClass, cn, daysAgo } from "@/lib/utils";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { FieldLabel, Input, Select } from "./ui/input";
import { TBody, TD, TH, THead, TR, Table } from "./ui/table";

const SIGNAL_SHORT: Record<number, string> = {
  1: "Volume",
  2: "Decline rate",
  3: "Latency",
  4: "Feedback",
  5: "Tenure",
  6: "Availability",
};

interface Props {
  onLogIntervention: (item: InterpreterListItem) => void;
}

export function InterpreterTable({ onLogIntervention }: Props) {
  const [band, setBand] = useState<Band | "">("");
  const [language, setLanguage] = useState<string>("");
  const [minTenure, setMinTenure] = useState<string>("");
  const [maxSilent, setMaxSilent] = useState<string>("");

  const filters: InterpreterFilters = useMemo(
    () => ({
      band: band || undefined,
      language: language || undefined,
      min_tenure_days: minTenure ? Number(minTenure) : undefined,
      max_days_since_last_session: maxSilent ? Number(maxSilent) : undefined,
      limit: 100,
    }),
    [band, language, minTenure, maxSilent]
  );

  const { data, isLoading, isError } = useQuery({
    queryKey: ["interpreters", filters],
    queryFn: () => listInterpreters(filters),
  });

  const activeFilterCount = [band, language, minTenure, maxSilent].filter(Boolean).length;

  return (
    <div className="rounded-lg border border-neutral-200 bg-white shadow-sm">
      {/* Filters bar */}
      <div className="grid grid-cols-2 gap-4 border-b border-neutral-100 p-4 md:grid-cols-5">
        <div>
          <FieldLabel htmlFor="f-band">Band</FieldLabel>
          <Select id="f-band" value={band} onChange={(e) => setBand(e.target.value as Band | "")}>
            <option value="">All</option>
            <option value="red">Red</option>
            <option value="yellow">Yellow</option>
            <option value="green">Green</option>
          </Select>
        </div>
        <div>
          <FieldLabel htmlFor="f-lang">Language</FieldLabel>
          <Input
            id="f-lang"
            placeholder="e.g. es"
            value={language}
            onChange={(e) => setLanguage(e.target.value.toLowerCase())}
            maxLength={8}
          />
        </div>
        <div>
          <FieldLabel htmlFor="f-tenure">Min tenure (days)</FieldLabel>
          <Input
            id="f-tenure"
            type="number"
            min={0}
            value={minTenure}
            onChange={(e) => setMinTenure(e.target.value)}
            placeholder="0"
          />
        </div>
        <div>
          <FieldLabel htmlFor="f-silent">Silent within (days)</FieldLabel>
          <Input
            id="f-silent"
            type="number"
            min={1}
            value={maxSilent}
            onChange={(e) => setMaxSilent(e.target.value)}
            placeholder="14"
          />
        </div>
        <div className="flex items-end">
          <Button
            variant="outline"
            className="w-full"
            onClick={() => {
              setBand("");
              setLanguage("");
              setMinTenure("");
              setMaxSilent("");
            }}
            disabled={activeFilterCount === 0}
          >
            Reset filters
          </Button>
        </div>
      </div>

      {/* Table */}
      {isLoading && (
        <div className="p-8 text-center text-sm text-neutral-500">Loading roster…</div>
      )}
      {isError && (
        <div className="flex items-center gap-2 p-8 text-sm text-red-700">
          <AlertTriangle className="h-4 w-4" />
          Could not load interpreters. Is the API running at
          <code className="rounded bg-neutral-100 px-1 font-mono text-xs">
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
          </code>
          ?
        </div>
      )}
      {data && (
        <>
          <Table>
            <THead>
              <TR>
                <TH className="w-[26%]">Interpreter</TH>
                <TH className="w-[14%]">Languages</TH>
                <TH className="w-[10%]">Tenure</TH>
                <TH className="w-[10%]">Score</TH>
                <TH className="w-[16%]">Top signal</TH>
                <TH className="w-[12%]">Last session</TH>
                <TH className="w-[12%] text-right">Action</TH>
              </TR>
            </THead>
            <TBody>
              {data.items.map((item) => (
                <TR
                  key={item.id}
                  className={cn(
                    "border-l-4",
                    item.latest_score
                      ? bandBorderClass(item.latest_score.band)
                      : "border-l-neutral-200"
                  )}
                >
                  <TD>
                    <div className="font-medium text-neutral-900">{item.full_name}</div>
                    <div className="font-mono text-xs text-neutral-500">
                      {item.external_id}
                    </div>
                  </TD>
                  <TD>
                    <div className="flex flex-wrap gap-1">
                      {item.languages.map((l) => (
                        <Badge
                          key={l}
                          className="bg-neutral-100 text-neutral-700 ring-neutral-200"
                        >
                          {l}
                        </Badge>
                      ))}
                    </div>
                  </TD>
                  <TD>
                    <span className="text-neutral-700">
                      {(item.tenure_days / 30.44).toFixed(1)} mo
                    </span>
                  </TD>
                  <TD>
                    {item.latest_score ? (
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-semibold tabular-nums text-neutral-900">
                          {item.latest_score.composite_score}
                        </span>
                        <Badge className={bandBadgeClass(item.latest_score.band)}>
                          {item.latest_score.band}
                        </Badge>
                      </div>
                    ) : (
                      <span className="text-neutral-400">—</span>
                    )}
                  </TD>
                  <TD>
                    <span className="text-sm text-neutral-700">
                      {item.latest_score?.top_signal_key
                        ? SIGNAL_SHORT[item.latest_score.top_signal_key]
                        : "—"}
                    </span>
                  </TD>
                  <TD>
                    <span className="text-sm text-neutral-600">
                      {daysAgo(item.last_session_at)}
                    </span>
                  </TD>
                  <TD className="text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onLogIntervention(item)}
                    >
                      Log intervention
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
          <div className="border-t border-neutral-100 px-4 py-3 text-xs text-neutral-500">
            Showing {data.items.length} of {data.total.toLocaleString()} interpreters
            {activeFilterCount > 0 && ` (${activeFilterCount} filter${activeFilterCount > 1 ? "s" : ""} applied)`}
          </div>
        </>
      )}
    </div>
  );
}
