import socket


class ProxyError(Exception):
    pass


def forward_command(target_ip: str, target_port: int, line: str, timeout_sec: float) -> str:
    try:
        with socket.create_connection((target_ip, target_port), timeout=timeout_sec) as s:
            s.settimeout(timeout_sec)
            s.sendall(line.encode("utf-8") + b"\n")

            data = b""
            while not data.endswith(b"\n"):
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk

            if not data:
                raise ProxyError("Cílová banka neodpověděla.")
            return data.decode("utf-8", errors="replace").strip()

    except (socket.timeout, TimeoutError):
        raise ProxyError("Timeout při komunikaci s cílovou bankou.")
    except OSError as e:
        raise ProxyError(f"Nelze se připojit na cílovou banku: {e}")