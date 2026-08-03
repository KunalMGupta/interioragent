#!/usr/bin/env bash
# Launch the InteriorAgent MCP server from any clone location (referenced by .mcp.json,
# which runs it with cwd = repo root).
# Python resolution: $IDSDL_PYTHON > the interioragent conda env if present > python3 on PATH.
cd "$(dirname "$0")/.."
PY="${IDSDL_PYTHON:-}"
if [ -z "$PY" ]; then
  for root in /opt/conda "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/mambaforge"; do
    if [ -x "$root/envs/interioragent/bin/python" ]; then
      PY="$root/envs/interioragent/bin/python"
      break
    fi
  done
fi
if [ -z "$PY" ] && command -v conda >/dev/null 2>&1; then
  base="$(conda info --base 2>/dev/null)"
  [ -n "$base" ] && [ -x "$base/envs/interioragent/bin/python" ] && PY="$base/envs/interioragent/bin/python"
fi
PY="${PY:-python3}"
if ! "$PY" -c "import mcp" >/dev/null 2>&1; then
  echo "[interioragent-mcp] ERROR: '$PY' cannot import the 'mcp' package." >&2
  echo "[interioragent-mcp] Install deps into the interioragent env (pip install -r requirements.txt)," >&2
  echo "[interioragent-mcp] or point IDSDL_PYTHON at the right interpreter." >&2
  exit 1
fi
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m IDSDL.service.mcp_server
