import logging


def setup_logging(cfg: dict) -> logging.Logger:
    log_cfg = cfg["logging"]
    level = getattr(logging, str(log_cfg.get("level", "INFO")).upper(), logging.INFO)

    logger = logging.getLogger("bank_node")
    logger.setLevel(level)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    fh = logging.FileHandler(log_cfg.get("file", "logs/bank.log"), encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger