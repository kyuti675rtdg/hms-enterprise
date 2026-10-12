"""Persistent PostgreSQL control script for HMS Enterprise.

Uses the pgserver-bundled Postgres binaries (installed in the project venv,
which lives under the home directory and therefore survives VM restarts).
The data directory is <project>/.pgdata, also persistent.

Postgres refuses to run as root, so this script must be executed as a
non-root user, e.g.:
    setpriv --reuid=65534 --regid=65534 --clear-groups \
        /home/hatch/workspace/hms-enterprise/.venv/bin/python scripts/db.py start

Usage: python scripts/db.py [init|start|stop|restart|status]
"""
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PGDATA = PROJECT / ".pgdata"
VENV_PY = PROJECT / ".venv" / "bin" / "python"
PORT = 5432

sys.path.insert(0, str(PROJECT / ".venv" / "lib" / "python3.12" / "site-packages"))
import pgserver  # noqa: E402


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True)


def conf_tuned():
    conf = PGDATA / "postgresql.conf"
    text = conf.read_text()
    wanted = {"port": str(PORT), "listen_addresses": "'localhost'"}
    for key, val in wanted.items():
        line = f"{key} = {val}"
        found = False
        out = []
        for l in text.splitlines():
            if l.strip().startswith(key + " ") or l.strip().startswith(key + "="):
                out.append(line)
                found = True
            else:
                out.append(l)
        if not found:
            out.append(line)
        text = "\n".join(out) + "\n"
    conf.write_text(text)


def cmd_init():
    if (PGDATA / "PG_VERSION").exists():
        print("data dir already initialized")
        return
    print("initializing data dir...")
    pgserver.initdb(["-U", "hms", "--auth=trust"], pgdata=PGDATA)
    conf_tuned()
    print("init done")


def cmd_start():
    print("starting postgres...")
    pgserver.pg_ctl(["-l", str(PGDATA / "logfile"),
                     "-w", "-t", "60", "start"], pgdata=PGDATA)
    for _ in range(30):
        r = sh("true")
        try:
            out = pgserver.psql(["-h", "localhost", "-p", str(PORT),
                                 "-U", "hms", "-d", "postgres",
                                 "-tAc", "select 1"])
            if out.strip() == "1":
                print(f"postgres accepting connections on localhost:{PORT}")
                return
        except Exception:
            pass
        time.sleep(1)
    print("WARNING: postgres did not become ready in time")
    sys.exit(1)


def cmd_stop():
    print("stopping postgres...")
    pgserver.pg_ctl(["-m", "fast", "stop"], pgdata=PGDATA)
    print("stopped")


def cmd_status():
    out = pgserver.pg_ctl(["status"], pgdata=PGDATA)
    print(out)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "init":
        cmd_init()
    elif action == "start":
        cmd_start()
    elif action == "stop":
        cmd_stop()
    elif action == "restart":
        cmd_stop()
        time.sleep(2)
        cmd_start()
    else:
        cmd_status()
