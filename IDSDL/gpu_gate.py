"""Cross-process GPU admission control for Blender renders.

Why this exists: a scene build is overwhelmingly CPU/network work (asset retrieval,
program execution) with a short GPU burst at the end — measured on this repo's own
examples, ~205 s of build against ~7 s of render. So many agents can build in
parallel; what must not happen is twenty Blender processes reaching for two cards at
the same instant. A CUDA OOM there is especially nasty because it can leave a
truncated output file that still passes an exists() check.

This module is the narrow gate: every render in IDSDL goes through
``SceneRenderer.run``, which wraps the Blender call in :func:`gpu_slot`. Holders are
counted across PROCESSES via ``flock`` on slot files, so independent agents — each
with its own MCP server — share one budget. A waiter blocks until a slot frees
rather than failing, which is what keeps utilization flat instead of spiky.

Knobs (all optional):
    IDSDL_GPU_SLOTS        concurrent renders allowed (default: 2 per detected GPU).
                           Set 0 to disable the gate entirely (legacy behaviour).
    IDSDL_GPU_MIN_FREE_MIB free VRAM a card must show to be chosen (default 2500).
    IDSDL_GPU_WAIT_S       give up waiting after this many seconds (default 1800).
    IDSDL_GPU_SLOT_DIR     where slot files live (default: <tmpdir>/idsdl_gpu_slots).
                           Agents that must share a budget need the same directory.
"""
import contextlib
import fcntl
import os
import subprocess
import tempfile
import time

_DEF_MIN_FREE_MIB = 2500
_DEF_WAIT_S = 1800.0
_POLL_S = 2.0


def _gpu_free_mib():
    """[(index, free_mib)] per visible card, or [] if nvidia-smi is unavailable."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return []
        rows = []
        for line in out.stdout.strip().splitlines():
            idx, free = (p.strip() for p in line.split(","))
            rows.append((int(idx), int(free)))
        return rows
    except Exception:
        return []


def _slot_count():
    """Slots allowed, 0 = ungated.

    OFF unless IDSDL_GPU_SLOTS is set. A single-agent run has nothing to contend
    with, and defaulting to on would mean a solo user whose card is briefly busy
    (another app, a stray Blender) starts WAITING where they used to render. Opt in
    when you actually run agents in parallel; "auto" sizes it at 2 per detected card.
    """
    raw = os.environ.get("IDSDL_GPU_SLOTS")
    if raw is None:
        return 0
    if raw.strip().lower() == "auto":
        gpus = len(_gpu_free_mib())
        return 2 * gpus if gpus else 0
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def _slot_dir():
    d = os.environ.get("IDSDL_GPU_SLOT_DIR") or os.path.join(
        tempfile.gettempdir(), "idsdl_gpu_slots")
    os.makedirs(d, exist_ok=True)
    return d


@contextlib.contextmanager
def gpu_slot(label="render"):
    """Hold one render slot; yields the GPU index to use, or None if ungated.

    Ungated (yields None immediately) when IDSDL_GPU_SLOTS=0, when no NVIDIA card is
    visible, or when the slot directory cannot be used — the gate must never be the
    reason a render fails to start.
    """
    n = _slot_count()
    if n <= 0:
        yield None
        return

    try:
        d = _slot_dir()
    except OSError:
        yield None
        return

    min_free = int(os.environ.get("IDSDL_GPU_MIN_FREE_MIB", _DEF_MIN_FREE_MIB))
    deadline = time.time() + float(os.environ.get("IDSDL_GPU_WAIT_S", _DEF_WAIT_S))
    handle, waited = None, False

    try:
        while True:
            for i in range(n):
                f = open(os.path.join(d, f"slot{i}.lock"), "a+")
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    f.close()
                    continue
                # Slot acquired — now choose a card. Free VRAM alone is a poor
                # signal here: a render that just started has not allocated yet, so
                # two slots taken seconds apart both see the same "emptiest" card and
                # pile onto it while the other idles. So spread by SLOT INDEX across
                # the cards that clear the floor, and let free VRAM decide only when
                # one card is genuinely far emptier than the rest.
                cards = _gpu_free_mib()
                if cards:
                    eligible = [c for c in cards if c[1] >= min_free]
                    if not eligible:
                        # everything is busy: drop the slot and wait rather than
                        # start a render that may OOM
                        fcntl.flock(f, fcntl.LOCK_UN)
                        f.close()
                        break
                    eligible.sort(key=lambda c: c[1], reverse=True)
                    if len(eligible) > 1 and (eligible[0][1] - eligible[1][1]) < 2048:
                        idx = eligible[i % len(eligible)][0]     # comparable -> spread
                    else:
                        idx = eligible[0][0]                     # one is clearly freer
                else:
                    idx = None
                handle = f
                break

            if handle is not None:
                if waited:
                    print(f"[gpu_gate] {label}: slot acquired"
                          + (f" on GPU {idx}" if idx is not None else ""))
                yield idx
                return

            if time.time() >= deadline:
                raise TimeoutError(
                    f"[gpu_gate] {label}: no GPU slot after "
                    f"{os.environ.get('IDSDL_GPU_WAIT_S', _DEF_WAIT_S)}s "
                    f"({n} slots, min free {min_free} MiB). Raise IDSDL_GPU_SLOTS or "
                    f"IDSDL_GPU_WAIT_S, or set IDSDL_GPU_SLOTS=0 to disable gating.")
            if not waited:
                print(f"[gpu_gate] {label}: waiting for a free GPU slot ({n} in use)...")
                waited = True
            time.sleep(_POLL_S)
    finally:
        if handle is not None:
            try:
                fcntl.flock(handle, fcntl.LOCK_UN)
            finally:
                handle.close()
