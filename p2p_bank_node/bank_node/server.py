import socket
import threading

from .logging_setup import setup_logging
from .protocol import parse_command, validate_and_normalize, ProtocolError
from .bank import Bank, BankError
from .proxy import forward_command, ProxyError


def _recv_line(conn: socket.socket) -> str | None:
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(4096)
        if not chunk:
            return None
        data += chunk
    return data.decode("utf-8", errors="replace").strip()


def _handle_client(conn: socket.socket, addr, cfg, bank: Bank, logger):
    idle_timeout = float(cfg["timeouts"]["client_idle_timeout_sec"])
    proxy_timeout = float(cfg["timeouts"]["proxy_timeout_sec"])
    bank_ip = cfg["bank"]["ip"]
    bank_port = int(cfg["bank"]["port"])

    conn.settimeout(idle_timeout)
    logger.info(f"client_connected client={addr[0]}:{addr[1]}")

    try:
        while True:
            try:
                line = _recv_line(conn)
                if line is None:
                    logger.info(f"client_closed client={addr[0]}:{addr[1]}")
                    return
            except socket.timeout:
                logger.info(f"client_timeout client={addr[0]}:{addr[1]}")
                return

            if not line:
                conn.sendall(b"ER Prazdny prikaz.\n")
                continue

            logger.info(f'client={addr[0]}:{addr[1]} line="{line}"')

            try:
                code, args = parse_command(line)
                cmd = validate_and_normalize(code, args)

                if cmd["code"] in ("AD", "AW", "AB") and cmd.get("bank_ip") != bank_ip:
                    target_ip = cmd["bank_ip"]
                    resp = forward_command(target_ip, bank_port, line, proxy_timeout)
                    logger.info(f'proxy target={target_ip}:{bank_port} resp="{resp}"')
                    conn.sendall((resp + "\n").encode("utf-8"))
                    continue

                c = cmd["code"]
                if c == "BC":
                    resp = f"BC {bank_ip}"
                elif c == "AC":
                    acct = bank.create_account()
                    resp = f"AC {acct}/{bank_ip}"
                elif c == "AD":
                    bank.deposit(cmd["account"], cmd["amount"])
                    resp = "AD"
                elif c == "AW":
                    bank.withdraw(cmd["account"], cmd["amount"])
                    resp = "AW"
                elif c == "AB":
                    bal = bank.balance(cmd["account"])
                    resp = f"AB {bal}"
                elif c == "AR":
                    bank.remove(cmd["account"])
                    resp = "AR"
                elif c == "BA":
                    resp = f"BA {bank.total_amount()}"
                elif c == "BN":
                    resp = f"BN {bank.number_of_clients()}"
                else:
                    raise ProtocolError("Nepovolený příkaz.")

                conn.sendall((resp + "\n").encode("utf-8"))
                logger.info(f'client={addr[0]}:{addr[1]} resp="{resp}"')

            except (ProtocolError, BankError) as e:
                msg = str(e)
                logger.warning(f'client={addr[0]}:{addr[1]} error="{msg}"')
                conn.sendall(("ER " + msg + "\n").encode("utf-8"))
            except ProxyError as e:
                msg = f"Proxy chyba: {e}"
                logger.warning(f'client={addr[0]}:{addr[1]} error="{msg}"')
                conn.sendall(("ER " + msg + "\n").encode("utf-8"))
            except Exception as e:
                msg = f"Chyba v aplikaci, prosím zkuste to později. ({e})"
                logger.exception(msg)
                conn.sendall(("ER " + msg + "\n").encode("utf-8"))

    finally:
        try:
            conn.close()
        except Exception:
            pass


def run_server(cfg: dict):
    logger = setup_logging(cfg)

    bank_ip = cfg["bank"]["ip"]
    bank_port = int(cfg["bank"]["port"])
    data_file = cfg["storage"]["data_file"]

    bank = Bank(bank_ip=bank_ip, data_file=data_file, logger=logger)
    bank.load_from_disk()

    logger.info(f"Starting bank node on {bank_ip}:{bank_port}, data_file={data_file}")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((bank_ip, bank_port))
    srv.listen(50)

    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=_handle_client, args=(conn, addr, cfg, bank, logger), daemon=True)
        t.start()