export default function Header() {
  return (
    <header className="relative z-20 flex items-center justify-center gap-2.5 pt-6 pb-2 sm:pt-8">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-gold/60" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-gold shadow-[0_0_8px_#e2b357]" />
      </span>
      <h1 className="text-sm font-bold uppercase tracking-[0.18em] text-white">
        Dharohar<span className="text-gold">Grid</span>
      </h1>
    </header>
  );
}
