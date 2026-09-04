import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// If the env vars aren't set (e.g. running the UI shell standalone before
// Phase 2 credentials exist), we don't want a hard crash on import — every
// caller checks `isSupabaseConfigured` and falls back to mock data instead.
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

if (!isSupabaseConfigured) {
  console.warn(
    "[DharoharGrid] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are not set. " +
      "Falling back to local mock graph data — see .env.example."
  );
}
