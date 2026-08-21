export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-8">
      <div className="flex items-center gap-3 text-xs font-medium uppercase tracking-widest text-neutral-500">
        <span className="h-px w-8 bg-neutral-400" />
        Day 1 scaffold
      </div>
      <h1 className="text-5xl font-semibold tracking-tight text-neutral-900">
        ChurnScope
      </h1>
      <p className="max-w-xl text-lg leading-relaxed text-neutral-600">
        Interpreter attrition early-warning dashboard. Signals go live on Day 6.
        For now, the API is at <code className="rounded bg-neutral-100 px-1.5 py-0.5 font-mono text-sm">/health</code>.
      </p>
      <div className="mt-4 text-xs font-mono uppercase tracking-widest text-neutral-400">
        prototype/interpreter-attrition · toospoint
      </div>
    </main>
  );
}
