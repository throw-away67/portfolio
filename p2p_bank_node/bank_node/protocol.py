import re

ACCOUNT_RE = re.compile(r"^(?P<acct>\d{5})/(?P<ip>\d{1,3}(\.\d{1,3}){3})$")


class ProtocolError(Exception):
    pass


def _parse_account_bank(token: str) -> tuple[int, str]:
    m = ACCOUNT_RE.match(token.strip())
    if not m:
        raise ProtocolError("Formát čísla účtu není správný.")
    acct = int(m.group("acct"))
    ip = m.group("ip")
    if acct < 10000 or acct > 99999:
        raise ProtocolError("Číslo účtu musí být v rozsahu 10000 až 99999.")
    return acct, ip


def _parse_amount(token: str) -> int:
    if not token.isdigit():
        raise ProtocolError("Částka není ve správném formátu.")
    amount = int(token)
    if amount < 0 or amount > 9223372036854775807:
        raise ProtocolError("Částka je mimo povolený rozsah.")
    return amount


def parse_command(line: str) -> tuple[str, list[str]]:
    raw = line.strip()
    if not raw:
        raise ProtocolError("Prázdný příkaz.")
    parts = raw.split()
    code = parts[0].upper()
    args = parts[1:]
    return code, args


def validate_and_normalize(code: str, args: list[str]) -> dict:
    if code == "BC":
        if args:
            raise ProtocolError("BC nemá argumenty.")
        return {"code": "BC"}

    if code == "AC":
        if args:
            raise ProtocolError("AC nemá argumenty.")
        return {"code": "AC"}

    if code in ("AD", "AW"):
        if len(args) != 2:
            raise ProtocolError("Špatný počet argumentů.")
        acct, ip = _parse_account_bank(args[0])
        amount = _parse_amount(args[1])
        return {"code": code, "account": acct, "bank_ip": ip, "amount": amount}

    if code in ("AB", "AR"):
        if len(args) != 1:
            raise ProtocolError("Špatný počet argumentů.")
        acct, ip = _parse_account_bank(args[0])
        return {"code": code, "account": acct, "bank_ip": ip}

    if code in ("BA", "BN"):
        if args:
            raise ProtocolError(f"{code} nemá argumenty.")
        return {"code": code}

    raise ProtocolError("Nepovolený příkaz.")