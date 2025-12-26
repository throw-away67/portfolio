from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    sslmode: str = "disable"


@dataclass(frozen=True)
class BusinessConfig:
    default_hourly_rate: float = 650.0


@dataclass(frozen=True)
class AppConfig:
    name: str
    log_level: str
    db: DbConfig
    business: BusinessConfig


def load_config(path: str | Path) -> AppConfig:
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Config file not found: {p.resolve()}")

    if tomllib is None:
        raise ConfigError("tomllib not available. Use Python 3.11+.")

    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise ConfigError(f"Failed to read config TOML: {e}") from e

    try:
        app = data["app"]
        db = data["db"]
        business = data.get("business", {})
        return AppConfig(
            name=str(app.get("name", "ServiceDesk")),
            log_level=str(app.get("log_level", "INFO")),
            db=DbConfig(
                host=str(db["host"]),
                port=int(db.get("port", 5432)),
                name=str(db["name"]),
                user=str(db["user"]),
                password=str(db["password"]),
                sslmode=str(db.get("sslmode", "disable")),
            ),
            business=BusinessConfig(
                default_hourly_rate=float(business.get("default_hourly_rate", 650.0))
            ),
        )
    except KeyError as e:
        raise ConfigError(f"Missing config key: {e}") from e
    except Exception as e:
        raise ConfigError(f"Invalid config values: {e}") from e