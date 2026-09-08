import { useState } from "react";

export default function SearchBar({ onSearch, disabled }) {
  const [value, setValue] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (value.trim()) onSearch(value.trim());
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="liquid-glass absolute bottom-4 right-4 z-20 flex w-[min(260px,60vw)] items-center gap-2 rounded-full border border-hairline-strong bg-white/[0.06] px-3.5 py-2 backdrop-blur-glass shadow-glass transition-colors focus-within:border-gold/50 sm:bottom-6 sm:right-6"
    >
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="shrink-0 text-white/50"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m21 21-4.35-4.35" />
      </svg>
      <input
        type="text"
        value={value}
        disabled={disabled}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Find a node…"
        className="w-full bg-transparent text-sm text-white placeholder:text-white/35 focus:outline-none disabled:opacity-40"
      />
    </form>
  );
}
