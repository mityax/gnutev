#!/usr/bin/python3

import logging
import os.path
import datetime
import sys
from itertools import groupby
from typing import Iterable, List, Callable

import src.datev_file as dt
import src.gnucash_file as gc
from src.utils import yearly_split, truncate_string, parse_any_date


def convert_gnucash_to_datev(gnucash_accounts_export_fd: Iterable[str],
                             gnucash_bookings_export_fd: Iterable[str],
                             start_date: datetime.date | None = None,
                             end_date: datetime.date | None = None,
                             financial_year_start: datetime.date | None = None,
                             skr_number: str = dt.DEFAULT_SKR_NUMBER,
                             title: str | None = None,
                             datev_output_dir: str = os.path.realpath('.'),
                             datev_output_file_title: str | None = None,
                             print_message_function: Callable[[str], None] = lambda _: None):
    accounts_file = gc.AccountsCSVFile.load_csv_export(gnucash_accounts_export_fd)
    bookings_file = gc.BookingsCSVFile.load_csv_export(gnucash_bookings_export_fd)

    start_date = start_date or min(d.date for d in bookings_file.rows)
    end_date = end_date or max(d.date for d in bookings_file.rows)

    periods = list(yearly_split(end_date, start_date))

    print_message_function(f"Converting transactions from {start_date} to {end_date} ({len(periods)} {'period' if len(periods) == 1 else 'periods'})…")

    for current_period, (start, end) in enumerate(periods):  # DATEV requires one CSV file per year
        if financial_year_start and current_period == 0:  # for the first period, we respect `financial_year_start`, if it is given
            current_fin_year_start = financial_year_start
        else:
            current_fin_year_start = datetime.date(start.year, 1, 1)

        datev_file = dt.BookingsCSVFile(
            start_date=start,
            end_date=end,
            financial_year_start=current_fin_year_start,
            skr_number=skr_number,
            title=title or f'Buchungen {start_date.strftime("%Y-%m")} bis {end_date.strftime("%Y-%m")}',
        )

        filtered_bookings = tuple(filter(  # query all bookings in the current period's year
            lambda b: b.date.year == start.year,
            bookings_file.rows
        ))

        for transaction_id, splits in groupby(filtered_bookings, key=lambda b: b.transaction_id):
            splits: List[gc.Booking] = list(splits)

            debit_splits = [b for b in splits if b.amount_num < 0]
            credit_splits = [b for b in splits if b.amount_num > 0]

            if len(debit_splits) > 1 and len(credit_splits) > 1:
                logging.error(f"Transaction: {debit_splits[0].description}")
                logging.error(f"  - Debit splits:")
                for b in debit_splits:
                    logging.error(f"    - {b.amount_with_sym} in {accounts_file.get_account_by_full_name(b.full_account_name).account_code} \"{b.full_account_name}\"")
                logging.error(f"  - Credit splits:")
                for b in credit_splits:
                    logging.error(f"    - {b.amount_with_sym} in {accounts_file.get_account_by_full_name(b.full_account_name).account_code} \"{b.full_account_name}\"")
                raise RuntimeError("There is more than one split for both, debit and credit. Thus there's an\n"
                                   "ambiguity in how to convert these splits into multiple bookings (which has\n"
                                   "to be done because DATEV doesn't support split transactions). This ambiguity\n"
                                   "can (at least to my knowledge) not easily be resolved. Consider creating\n"
                                   "separate split transactions in GnuCash, such that there's either exactly\n"
                                   "one debit split or exactly one credit split.\n"
                                   "See above for details about the transaction.")

            if len(debit_splits) > 1:
                bookings, contra_booking = debit_splits, credit_splits[0],
            else:
                bookings, contra_booking = credit_splits, debit_splits[0]

            contra_account = accounts_file.get_account_by_full_name(contra_booking.full_account_name)

            if not contra_account:
                raise ValueError(f"Account \"{contra_booking.full_account_name}\" from booking \"{contra_booking.description}\" "
                                 f"cannot be found in the exported account file. This potentially indicates that the"
                                 f"supplied booking CSV export doesn't match the supplied accounts CSV export.")

            for booking in bookings:
                account = accounts_file.get_account_by_full_name(booking.full_account_name)

                if not account:
                    raise ValueError(f"Account \"{booking.full_account_name}\" from booking \"{booking.description}\" "
                                     f"cannot be found in the exported account file. This potentially indicates that "
                                     f"the supplied booking CSV export doesn't match the supplied accounts CSV export.")

                datev_file.add_booking(
                    revenue=abs(booking.amount_num),
                    document_date=booking.date,
                    posting_text=truncate_string(booking.description, 60),
                    account=int(account.account_code),
                    contra_account_without_bu_key=int(contra_account.account_code),
                    debit_credit_indicator='S' if booking.amount_num > 0 else 'H',  # S = debit, H = credit
                    additional_info_type_1="OriginalGnuCashTransactionId",
                    additional_info_content_1=transaction_id,
                    additional_info_type_2='OriginalTransactionDescription' if len(booking.description) > 60 else None,
                    additional_info_content_2=truncate_string(booking.description, 210) if len(booking.description) > 60 else None,
                )

        file_title = datev_output_file_title or title
        if file_title and len(periods) > 1:
            file_title += f"_{start.year}"
        fn = os.path.join(
            datev_output_dir,
            datev_file.get_suggested_filename(title=file_title)
        )

        with open(fn, "w+") as f:
            datev_file.to_csv(f)

        print_message_function(
            f" - Wrote output file {current_period+1}/{len(periods)} ({start} to {end}) "
            f"containing {len(set(b.transaction_id for b in filtered_bookings))} bookings to \"{fn}\"")

    print_message_function(f"{len(periods)} DATEV-compatible {'file' if len(periods) == 1 else 'files'} successfully created.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("accounts-csv-export", help="The path to the Account Tree CSV file exported from GnuCash")
    parser.add_argument("transactions-csv-export", help="The path to the Transactions CSV file exported from GnuCash")

    parser.add_argument("--financial-year-start", default=None, help="Start of the financial year in YYYY-MM-DD. If omitted, Jan 1 is used for each year")
    parser.add_argument("--output-folder", default=os.path.realpath("."), help="Path to the output folder to place DATEV files in. Default: current folder")
    parser.add_argument("--title", default=None, help="Title of the exported DATEV files")

    args = parser.parse_args(sys.argv[1:])

    with open(getattr(args, 'accounts-csv-export')) as accountsfd:
        with open(getattr(args, 'transactions-csv-export')) as bookingsfd:
            convert_gnucash_to_datev(
                gnucash_accounts_export_fd=accountsfd,
                gnucash_bookings_export_fd=bookingsfd,
                datev_output_dir=args.output_folder,
                title=args.title,
                financial_year_start=parse_any_date(args.financial_year_start),
                print_message_function=print,
            )
