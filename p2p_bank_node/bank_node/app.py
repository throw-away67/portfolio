import os

from p2p_bank_node.libs.pvl_cli import build_parser
from p2p_bank_node.libs.pvl_config import load_yaml_config, ConfigError

from .server import run_server


def _validate_bank_config(cfg: dict) -> dict:
    if "bank" not in cfg or "timeouts" not in cfg or "storage" not in cfg or "logging" not in cfg:
        raise ConfigError("Config must contain 'bank', 'timeouts', 'storage', 'logging' sections.")

    bank = cfg["bank"]
    if "ip" not in bank:
        raise ConfigError("Missing bank.ip in config.")
    if "port" not in bank:
        raise ConfigError("Missing bank.port in config.")

    timeouts = cfg["timeouts"]
    timeouts.setdefault("client_idle_timeout_sec", 5.0)
    timeouts.setdefault("proxy_timeout_sec", 5.0)

    storage = cfg["storage"]
    if "data_file" not in storage:
        raise ConfigError("Missing storage.data_file in config.")

    logging_cfg = cfg["logging"]
    logging_cfg.setdefault("level", "INFO")
    logging_cfg.setdefault("file", "logs/bank.log")

    return cfg


def main():
    parser = build_parser()
    args = parser.parse_args()

    cfg_path = args.config
    cfg = load_yaml_config(cfg_path)
    cfg = _validate_bank_config(cfg)

    os.makedirs(os.path.dirname(cfg["storage"]["data_file"]) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(cfg["logging"]["file"]) or ".", exist_ok=True)

    run_server(cfg)