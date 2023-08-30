import csv
from decimal import Decimal
from dataclasses import dataclass
import datetime
from typing import Iterable, List, T

from .utils import parse_any_date


class BookingsCSVFile:
    def __init__(self):
        self.header: List[str] = [
            'Date', 'Transaction ID', 'Number', 'Description', 'Notes', 'Commodity/Currency', 'Void Reason', 'Action',
            'Memo', 'Full Account Name', 'Account Name', 'Amount With Sym', 'Amount Num.', 'Value With Sym',
            'Value Num.', 'Reconcile', 'Reconcile Date', 'Rate/Price'
        ]
        self.rows: List[Booking] = []

    @classmethod
    def load_csv_export(cls, infd: Iterable[str]) -> 'BookingsCSVFile':
        reader = csv.reader(infd)

        file = cls()
        file.header = next(reader)

        for row in reader:
            file.rows.append(Booking(
                date=parse_any_date(row[0]),
                transaction_id=row[1],
                number=row[2],
                description=row[3],
                notes=row[4],
                commodity_currency=row[5],
                void_reason=row[6],
                action=row[7],
                memo=row[8],
                full_account_name=row[9],
                account_name=row[10],
                amount_with_sym=row[11],
                amount_num=Decimal(row[12].replace(",", "")),
                value_with_sym=row[13],
                value_num=Decimal(row[14].replace(",", "")),
                reconcile=row[15],
                reconcile_date=parse_any_date(row[16]) if row[16].strip() else None,
                rate_price=row[17],
            ))

        return file


class AccountsCSVFile:
    def __init__(self):
        self.header: List[str] = [
            'Type', 'Full Account Name', 'Account Name', 'Account Code', 'Description', 'Account Color', 'Notes',
            'Symbol', 'Namespace', 'Hidden', 'Tax Info', 'Placeholder'
        ]
        self.rows: List[Account] = []

    @classmethod
    def load_csv_export(cls, infd: Iterable[str]) -> 'AccountsCSVFile':
        reader = csv.reader(infd)

        file = cls()
        file.header = next(reader)

        for row in reader:
            file.rows.append(Account(
                type_=row[0],
                full_account_name=row[1],
                account_name=row[2],
                account_code=row[3],
                description=row[4],
                account_color=row[5],
                notes=row[6],
                symbol=row[7],
                namespace=row[8],
                hidden=row[9],
                tax_info=row[10],
                placeholder=row[11],
            ))

        return file

    def get_account_by_full_name(self, full_name: str, default: T = None) -> T | 'Account':
        return next(filter(
            lambda a: a.full_account_name == full_name,
            self.rows
        ), None)


@dataclass
class Booking:
    date: datetime.date  # Date of the financial transaction.
    transaction_id: str  # Unique ID for the transaction.
    number: str  # Transaction number.
    description: str  # Description of the transaction.
    notes: str  # Additional notes or comments for the transaction.
    commodity_currency: str  # Commodity or currency used in the transaction.
    void_reason: str  # Reason for voiding the transaction, if applicable.
    action: str  # Action related to the transaction.
    memo: str  # Memo or additional information related to the transaction.
    full_account_name: str  # Full account name.
    account_name: str  # Account name.
    amount_with_sym: str  # Amount with symbol or currency.
    amount_num: Decimal  # Numerical amount.
    value_with_sym: str  # Value with symbol or currency.
    value_num: Decimal  # Numerical value.
    reconcile: str  # Reconciliation status of the transaction.
    reconcile_date: datetime.date | None  # Reconciliation date of the transaction.
    rate_price: str  # Rate or price associated with the transaction.


@dataclass
class Account:
    type_: str  # Type of the account.
    full_account_name: str  # Full account name.
    account_name: str  # Account name.
    account_code: str  # Account code.
    description: str  # Description of the account.
    account_color: str  # Color associated with the account.
    notes: str  # Additional notes or comments for the account.
    symbol: str  # Symbol associated with the account.
    namespace: str  # Namespace of the account.
    hidden: str  # Indicates if the account is hidden.
    tax_info: str  # Tax information related to the account.
    placeholder: str  # Indicates if the account is a placeholder.
