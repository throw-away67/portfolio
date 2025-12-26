from __future__ import annotations

import sys

from servicedesk.config import ConfigError, load_config
from servicedesk.db import Db, DbError
from servicedesk.cli import run_cli


def main() -> int:
    try:
        cfg = load_config("config.toml")
        db = Db(cfg.db)
        run_cli(db, default_hourly_rate=cfg.business.default_hourly_rate)
        return 0
    except ConfigError as e:
        print(f"[CONFIG ERROR] {e}")
        return 2
    except DbError as e:
        print(f"[DB ERROR] {e}")
        return 3
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())