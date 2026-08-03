#!/usr/bin/env python3
"""Smoke-test the InteriorAgent MCP server exactly the way an MCP client would.

Run from the repo root with any Python 3 (stdlib only — the launcher resolves
the real interpreter itself):

    python3 tools/mcp_smoke.py              # handshake + tools/list + howto
    python3 tools/mcp_smoke.py --retrieve   # also do a real asset retrieval (~20 s)

Exit code 0 means a fresh MCP client (Claude Code, Claude Desktop, ...) will be
able to connect and call tools. On failure it prints the server's stderr, which
is where the launcher explains what is missing (conda env, mcp package, ...).
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARTUP_TIMEOUT = 180  # first boot loads the embedding matrices once


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retrieve", action="store_true",
                    help="also run a real asset retrieval (needs datasets + API key)")
    args = ap.parse_args()

    env = dict(os.environ)
    env_file = os.path.join(REPO, ".env")
    if os.path.exists(env_file):  # same file reload_credentials reads at runtime
        for line in open(env_file):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    proc = subprocess.Popen(
        [os.path.join(REPO, "tools", "interioragent_mcp.sh")], cwd=REPO, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    stderr_lines = []
    threading.Thread(
        target=lambda: stderr_lines.extend(l.rstrip() for l in proc.stderr),
        daemon=True).start()

    state = {"id": 0}

    def fail(msg):
        print(f"FAIL: {msg}")
        if stderr_lines:
            print("--- server stderr ---")
            print("\n".join(stderr_lines[-25:]))
        proc.terminate()
        sys.exit(1)

    def rpc(method, params=None, notify=False, timeout=60):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if notify:
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()
            return None
        state["id"] += 1
        msg["id"] = state["id"]
        try:
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()
        except BrokenPipeError:
            fail("server closed stdin (it exited during startup)")
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    fail(f"server exited with code {proc.returncode} during '{method}'")
                continue
            try:
                m = json.loads(line)
            except json.JSONDecodeError:
                continue
            if m.get("id") == state["id"]:
                if "error" in m:
                    fail(f"'{method}' returned an error: {json.dumps(m['error'])[:400]}")
                return m
        fail(f"timed out after {timeout}s waiting for '{method}'")

    def text_of(res):
        return "".join(c.get("text", "") for c in res["result"].get("content", [])
                       if c.get("type") == "text")

    t0 = time.time()
    init = rpc("initialize", {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "interioragent-smoke", "version": "1.0"},
    }, timeout=STARTUP_TIMEOUT)
    si = init["result"].get("serverInfo", {})
    print(f"[1/3] initialize OK in {time.time() - t0:.1f}s  "
          f"(server={si.get('name')}, protocol={init['result'].get('protocolVersion')})")
    rpc("notifications/initialized", notify=True)

    tools = rpc("tools/list", {})["result"]["tools"]
    names = sorted(t["name"] for t in tools)
    for required in ("howto", "retrieve", "run_scene", "flow_start"):
        if required not in names:
            fail(f"expected tool '{required}' missing from tools/list ({len(names)} tools)")
    print(f"[2/3] tools/list OK — {len(names)} tools")

    t0 = time.time()
    howto = text_of(rpc("tools/call", {"name": "howto", "arguments": {}}))
    if "InteriorAgent" not in howto:
        fail("howto returned unexpected content")
    print(f"[3/3] howto OK in {time.time() - t0:.1f}s")

    if args.retrieve:
        t0 = time.time()
        out = text_of(rpc("tools/call", {
            "name": "retrieve",
            "arguments": {"query": "a modern gray three-seat sofa"}}, timeout=180))
        first = out.splitlines()[1] if len(out.splitlines()) > 1 else out[:120]
        print(f"[4/3] retrieve OK in {time.time() - t0:.1f}s — {first.strip()}")

    proc.terminate()
    print("SMOKE TEST PASSED — an MCP client can connect to this checkout.")


if __name__ == "__main__":
    main()
