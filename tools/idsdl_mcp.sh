#!/usr/bin/env bash
# Launch the IDSDL MCP server from any clone location (referenced by .mcp.json,
# which runs it with cwd = repo root).
# Python resolution: $IDSDL_PYTHON > the interioragent conda env if present > python3 on PATH.
cd "$(dirname "$0")/.."
PY="${IDSDL_PYTHON:-}"
if [ -z "$PY" ] && [ -x /opt/conda/envs/interioragent/bin/python ]; then
  PY=/opt/conda/envs/interioragent/bin/python
fi
PY="${PY:-python3}"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m IDSDL.service.mcp_server
