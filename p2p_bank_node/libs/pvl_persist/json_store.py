import json
import os
import tempfile


class PersistenceError(Exception):
    pass


def load_json(path: str, default: dict) -> dict:
    """
    Pattern (load-on-start) inspired by:
    throw-away67/portfolio crawler/main.py (seen file load)
    https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/crawler/main.py#L18-L32
    """
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or default
    except Exception as e:
        raise PersistenceError(str(e))


def save_json_atomic(path: str, data: dict) -> None:
    try:
        d = os.path.dirname(path) or "."
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix="pvl_", suffix=".json", dir=d)
        os.close(fd)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        raise PersistenceError(str(e))