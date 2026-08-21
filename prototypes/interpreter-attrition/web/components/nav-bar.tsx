"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { backfillScores, recomputeScores } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";

const IS_DEV_UI = process.env.NEXT_PUBLIC_SHOW_DEV_UI !== "false";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/interventions", label: "Interventions" },
];

function isActive(href: string, pathname: string | null): boolean {
  if (!pathname) return false;
  if (href === "/") return pathname === "/" || pathname.startsWith("/interpreters/");
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function NavBar() {
  const pathname = usePathname();
  const qc = useQueryClient();
  const recompute = useMutation({
    mutationFn: async () => {
      await recomputeScores();
      await backfillScores(14);
    },
    onSuccess: () => qc.invalidateQueries(),
  });

  return (
    <nav className="sticky top-0 z-40 border-b border-neutral-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-8 px-6 md:px-10">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-sm font-semibold tracking-tight text-neutral-900">
            ChurnScope
          </span>
          <span className="hidden text-[10px] font-medium uppercase tracking-widest text-neutral-500 md:inline">
            Interpreter attrition
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                isActive(link.href, pathname)
                  ? "bg-neutral-100 text-neutral-900"
                  : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900"
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-3">
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
    </nav>
  );
}
