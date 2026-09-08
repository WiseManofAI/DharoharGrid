#!/usr/bin/env python
"""One-click setup + run for the whole DharoharGrid project.

Double-click start.bat (Windows) or run `python bootstrap.py` directly.
Safe to re-run any time — every step is idempotent and skips what's already
done (already-installed deps, an already-populated graph, already-running
servers on their ports).

What it does, in order:
  1. Makes sure this script's own light dependencies are present.
  2. Installs each of the three backends' requirements.txt.
  3. Applies Backend/schema.sql automatically IF a direct Postgres
     connection string is configured (SUPABASE_DB_URL in
     "Backend/Obsidian Backend/.env") — otherwise prints a one-time
     reminder to paste it into the Supabase SQL editor and moves on.
     (This is the one step the Supabase REST API genuinely can't do; a
     service-role API key isn't a database connection.)
  4. Runs the discovery-graph pipeline once if cultural_nodes is empty —
     this is what "just add the Supabase and LLM keys" actually triggers.
  5. Starts all three backend servers (skips any already running).
  6. Starts the frontend static server and opens the browser.

Everything logs into this one console window — closing it (or Ctrl+C) stops
every server it started.
"""
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = ROOT / "Backend"
BACKENDS = [
    ("AI Backend", 8001),
    ("Spatial Backend", 8002),
    ("Obsidian Backend", 8003),
]
FRONTEND_PORT = 8843


def banner(text):
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


def port_open(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def ensure_bootstrap_deps():
    banner("[1/6] Checking bootstrap's own dependencies")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "python-dotenv", "supabase"],
        check=False,
    )


def install_backend_deps():
    banner("[2/6] Installing backend dependencies (this can take a while the first time)")
    for folder, _ in BACKENDS:
        req = BACKEND_ROOT / folder / "requirements.txt"
        print(f"  - {folder}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)]
        )
        if result.returncode != 0:
            print(f"    ! install failed for {folder} (exit {result.returncode}) — continuing anyway.")


def apply_schema():
    banner("[3/6] Applying database schema")
    from dotenv import dotenv_values

    env_path = BACKEND_ROOT / "Obsidian Backend" / ".env"
    env = dotenv_values(env_path)
    db_url = env.get("SUPABASE_DB_URL") or env.get("DATABASE_URL")

    if not db_url:
        print("  No SUPABASE_DB_URL set yet in 'Backend/Obsidian Backend/.env'.")
        print("  One-time manual step until you add it: paste Backend/schema.sql")
        print("  into the Supabase SQL editor once, then re-run this script.")
        return

    try:
        import psycopg2
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psycopg2-binary"], check=False)
        import psycopg2

    schema_sql = (BACKEND_ROOT / "schema.sql").read_text(encoding="utf-8")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.close()
        print("  Schema applied.")
    except Exception as e:  # noqa: BLE001
        print(f"  ! Could not apply schema automatically: {e}")
        print("  Paste Backend/schema.sql into the Supabase SQL editor manually instead.")


def maybe_build_graph():
    banner("[4/6] Checking the discovery graph")
    from dotenv import dotenv_values

    obsidian_dir = BACKEND_ROOT / "Obsidian Backend"
    env = dotenv_values(obsidian_dir / ".env")
    url, key = env.get("SUPABASE_URL"), env.get("SUPABASE_KEY")
    if not url or not key:
        print("  Obsidian Backend .env is missing Supabase credentials — skipping.")
        return

    try:
        from supabase import create_client

        sb = create_client(url, key)
        count = sb.table("cultural_nodes").select("node_id", count="exact").limit(1).execute().count or 0
    except Exception as e:  # noqa: BLE001
        print(f"  Could not query cultural_nodes yet ({e}).")
        print("  This is expected if schema.sql hasn't been applied yet — see step 3 above.")
        return

    if count > 0:
        print(f"  Graph already has {count} node(s) — skipping the pipeline run.")
        print("  (To force a rebuild: cd \"Backend/Obsidian Backend\" && python -m app.pipeline.build_graph)")
        return

    print("  Graph is empty — running the full pipeline now.")
    print("  This calls the LLM a few hundred times (enrichment + dedupe + synapse")
    print("  adjudication) so it can take a while on first run. Safe to Ctrl+C and")
    print("  resume later with --from <step> (see the module's docstring).")
    subprocess.run([sys.executable, "-m", "app.pipeline.build_graph"], cwd=obsidian_dir, check=False)


def start_servers():
    banner("[5/6] Starting backend servers")
    procs = []
    for folder, port in BACKENDS:
        if port_open(port):
            print(f"  - {folder} already running on :{port}, leaving it alone")
            continue
        cwd = BACKEND_ROOT / folder
        p = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)], cwd=cwd)
        procs.append(p)
        print(f"  - {folder} starting on :{port} (pid {p.pid})")
    return procs


def start_frontend():
    banner("[6/6] Starting the frontend + opening your browser")
    procs = []
    if not port_open(FRONTEND_PORT):
        p = subprocess.Popen([sys.executable, "-m", "http.server", str(FRONTEND_PORT)], cwd=ROOT)
        procs.append(p)
        print(f"  - frontend starting on :{FRONTEND_PORT} (pid {p.pid})")
    else:
        print(f"  - frontend already running on :{FRONTEND_PORT}")

    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}/index.html")
    return procs


def main():
    banner("DharoharGrid — one-click setup & run")
    ensure_bootstrap_deps()
    install_backend_deps()
    apply_schema()
    try:
        maybe_build_graph()
    except Exception as e:  # noqa: BLE001
        print(f"  ! Pipeline step skipped due to an error: {e}")

    procs = start_servers()
    procs += start_frontend()

    banner("Everything that could start is running.")
    print("Close this window (or Ctrl+C) to stop every server it started.")
    print("Backend API docs: http://localhost:8001/docs  http://localhost:8002/docs  http://localhost:8003/docs\n")

    try:
        while True:
            if procs and any(p.poll() is not None for p in procs):
                print("\nOne of the servers exited — shutting the rest down.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()


if __name__ == "__main__":
    main()
