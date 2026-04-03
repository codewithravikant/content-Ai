"""Session debug NDJSON logger (agent instrumentation)."""
import json
import time
from pathlib import Path

_SESSION = "78b2f3"
_LOG = Path("/Users/ravikantpandit/koodsisu/ghostwriter/.cursor/debug-78b2f3.log")


def dbg(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict | None = None,
    run_id: str = "pre-fix",
) -> None:
    # region agent log
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": _SESSION,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
            "runId": run_id,
        }
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        pass
    # endregion
