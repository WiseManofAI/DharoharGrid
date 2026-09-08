export default function BackButton({ onClick, label = "Back" }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Go back"
      className="liquid-glass group fixed left-4 top-4 z-30 flex items-center gap-2 rounded-full border border-hairline-strong bg-white/5 py-2.5 pl-3 pr-4 text-sm font-medium text-white backdrop-blur-glass transition-all duration-300 hover:border-white/35 hover:bg-white/10 hover:shadow-[0_0_20px_rgba(255,255,255,0.12)] sm:left-6 sm:top-6"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="transition-transform duration-300 group-hover:-translate-x-0.5"
      >
        <path d="M19 12H5" />
        <path d="M12 19l-7-7 7-7" />
      </svg>
      {label}
    </button>
  );
}
