import argparse


def build_parser() -> argparse.ArgumentParser:
    """
    Reused/adapted style from:
    throw-away67/portfolio downloader/cli.py
    https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/downloader/cli.py
    """
    parser = argparse.ArgumentParser(description="P2P bank node (ESSENTIALS).")
    parser.add_argument("--config", default="config/config.yaml", help="Path to YAML config.")
    return parser