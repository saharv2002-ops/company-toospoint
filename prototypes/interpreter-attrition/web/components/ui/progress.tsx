import { cn } from "@/lib/utils";

interface Props {
  value: number;  // 0..100
  className?: string;
}

/**
 * Simple progress bar. Colour ramps green → yellow → red at 40 / 65
 * (matching band boundaries so the visual sits in one language).
 */
export function Progress({ value, className }: Props) {
  const v = Math.max(0, Math.min(100, value));
  const fill =
    v >= 65 ? "bg-band-red" : v >= 40 ? "bg-band-yellow" : "bg-band-green";
  return (
    <div className={cn("h-1.5 w-full overflow-hidden rounded-full bg-neutral-100", className)}>
      <div
        className={cn("h-full rounded-full transition-all", fill)}
        style={{ width: `${v}%` }}
      />
    </div>
  );
}
