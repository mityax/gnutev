#!/usr/bin/python3

import os
import subprocess
import traceback
from urllib.parse import unquote, urlparse

import main
from src.utils import parse_any_date


def _show_error_dialog(title: str, text: str):
    import subprocess

    if len(text.strip().splitlines()) == 1:
        dialog = subprocess.Popen(
            ['zenity', '--title', title, '--error', '--text', text.strip()],
            stdin=subprocess.PIPE,
        )
    else:
        dialog = subprocess.Popen([
            'zenity', '--title', title, '--text-info', '--no-wrap', '--font', 'Monospace', '--width=800', '--height=500'
        ], stdin=subprocess.PIPE)
        dialog.stdin.write(text.encode())
        dialog.stdin.flush()


if __name__ == '__main__':
    if not os.getenv('NAUTILUS_SCRIPT_SELECTED_FILE_PATHS') or not os.getenv('NAUTILUS_SCRIPT_CURRENT_URI'):
        raise RuntimeError("This script needs to be run from within the nautilus file manager.")

    selected_files = os.getenv('NAUTILUS_SCRIPT_SELECTED_FILE_PATHS', '').strip().splitlines()
    cwd = unquote(urlparse(os.getenv('NAUTILUS_SCRIPT_CURRENT_URI')).path)

    if len(selected_files) != 2 or any(not f.endswith('.csv') for f in selected_files):
        _show_error_dialog("Invalid Files Selected","Please select exactly two CSV files, one GnuCash "
                                                    "accounts tree export and one GnuCash transaction export.")
        exit(1)

    title, date = subprocess.check_output([
        'zenity', '--forms', '--title=GnuTev', '--text=Optionally, configure details for the conversion below.',
        '--add-entry=DATEV file title', '--add-entry=Financial year start'
    ], text=True).strip().split('|')

    logs = []  # log messages are stored in here during the conversion

    try:
        with open(selected_files[0]) as accounts_fd:
            with open(selected_files[1]) as bookings_fd:
                accounts_fd, bookings_fd = main.ensure_correct_exports_order(accounts_fd, bookings_fd, print_warning=False)

                # Run the conversion:
                datev_files = main.convert_gnucash_to_datev(
                    gnucash_accounts_export_fd=accounts_fd,
                    gnucash_bookings_export_fd=bookings_fd,
                    datev_output_dir=cwd,
                    title=title.strip() or None,
                    financial_year_start=parse_any_date(date.strip()) if date.strip() else None,
                    print_message_function=lambda text: logs.append(text),
                )

        subprocess.Popen(['notify-send', 'Conversion succeeded', f"{len(datev_files)} DATEV-compatible {'file' if len(datev_files) == 1 else 'files'} successfully created."]).communicate()
    except:
        _show_error_dialog('Conversion Failed', traceback.format_exc())
        raise


