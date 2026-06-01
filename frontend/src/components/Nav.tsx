"use client";

import Link from "next/link";

export function Nav() {
  return (
    <nav className="bg-slate-800 border-b border-slate-700">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
        <Link href="/" className="font-bold text-lg text-sky-400 hover:text-sky-300">
          EvalForge
        </Link>
        <Link href="/" className="text-sm text-slate-300 hover:text-white">
          Dashboard
        </Link>
        <Link href="/compare" className="text-sm text-slate-300 hover:text-white">
          Compare
        </Link>
      </div>
    </nav>
  );
}
