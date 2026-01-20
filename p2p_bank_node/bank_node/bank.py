import random
import threading

from p2p_bank_node.libs.pvl_persist import load_json, save_json_atomic, PersistenceError


class BankError(Exception):
    pass


class Bank:
    def __init__(self, bank_ip: str, data_file: str, logger):
        self.bank_ip = bank_ip
        self.data_file = data_file
        self.logger = logger
        self._lock = threading.Lock()
        self.accounts: dict[int, int] = {}

    def load_from_disk(self):
        raw = load_json(self.data_file, default={"accounts": {}})
        acc = {}
        for k, v in (raw.get("accounts") or {}).items():
            acc[int(k)] = int(v)
        self.accounts = acc
        self.logger.info(f"Loaded accounts: {len(self.accounts)}")

    def _persist(self):
        try:
            save_json_atomic(self.data_file, {"accounts": self.accounts})
        except PersistenceError as e:
            raise BankError(f"Chyba uložiště: {e}")

    def create_account(self) -> int:
        with self._lock:
            for _ in range(200000):
                acct = random.randint(10000, 99999)
                if acct not in self.accounts:
                    self.accounts[acct] = 0
                    self._persist()
                    return acct
            raise BankError("Nelze vytvořit nový účet.")

    def deposit(self, acct: int, amount: int) -> None:
        with self._lock:
            if acct not in self.accounts:
                raise BankError("Účet neexistuje.")
            bal = self.accounts[acct]
            new_bal = bal + amount
            if new_bal > 9223372036854775807:
                raise BankError("Přetečení částky (overflow).")
            self.accounts[acct] = new_bal
            self._persist()

    def withdraw(self, acct: int, amount: int) -> None:
        with self._lock:
            if acct not in self.accounts:
                raise BankError("Účet neexistuje.")
            bal = self.accounts[acct]
            if amount > bal:
                raise BankError("Není dostatek finančních prostředků.")
            self.accounts[acct] = bal - amount
            self._persist()

    def balance(self, acct: int) -> int:
        with self._lock:
            if acct not in self.accounts:
                raise BankError("Účet neexistuje.")
            return self.accounts[acct]

    def remove(self, acct: int) -> None:
        with self._lock:
            if acct not in self.accounts:
                raise BankError("Účet neexistuje.")
            if self.accounts[acct] != 0:
                raise BankError("Nelze smazat bankovní účet na kterém jsou finance.")
            del self.accounts[acct]
            self._persist()

    def total_amount(self) -> int:
        with self._lock:
            return sum(self.accounts.values())

    def number_of_clients(self) -> int:
        with self._lock:
            return len(self.accounts)