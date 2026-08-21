"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { createIntervention } from "@/lib/api";
import type { InterventionAction } from "@/lib/types";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { FieldLabel, Select } from "./ui/input";

const ACTIONS: { value: InterventionAction; label: string }[] = [
  { value: "coach_call", label: "Coach call" },
  { value: "assign_mentor", label: "Assign mentor" },
  { value: "schedule_flex", label: "Schedule flex" },
  { value: "comp_bonus", label: "Comp bonus" },
  { value: "no_action", label: "No action" },
];

interface Props {
  interpreterId: string | null;
  interpreterName?: string;
  onClose: () => void;
}

export function InterventionDialog({ interpreterId, interpreterName, onClose }: Props) {
  const [action, setAction] = useState<InterventionAction>("coach_call");
  const [notes, setNotes] = useState("");
  const qc = useQueryClient();

  useEffect(() => {
    if (interpreterId) {
      setAction("coach_call");
      setNotes("");
    }
  }, [interpreterId]);

  const mutation = useMutation({
    mutationFn: () =>
      createIntervention({
        interpreter_id: interpreterId!,
        action,
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interventions"] });
      qc.invalidateQueries({ queryKey: ["interpreters"] });
      onClose();
    },
  });

  return (
    <Dialog open={interpreterId !== null} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Log intervention</DialogTitle>
          <DialogDescription>
            {interpreterName ? `For ${interpreterName}` : "New intervention"}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div>
            <FieldLabel htmlFor="action">Action</FieldLabel>
            <Select
              id="action"
              value={action}
              onChange={(e) => setAction(e.target.value as InterventionAction)}
            >
              {ACTIONS.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <FieldLabel htmlFor="notes">Notes (optional)</FieldLabel>
            <textarea
              id="notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-950"
              placeholder="Context, agreed follow-up, etc."
            />
          </div>
          {mutation.isError && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
              Failed to save. Try again.
            </div>
          )}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!interpreterId || mutation.isPending}
          >
            {mutation.isPending ? "Saving…" : "Save intervention"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
