# GnuTev
Export GnuCash bookings to the german DATEV export format – such that they can directly be imported into DATEV-compatible applications.

## Installation

GnuTev requires you to have Python >= 3.8 installed on your system. Apart from that,
there's no extra dependencies.

To use GnuTev, just clone the repository.

## Usage

GnuTev uses GnuCash CSV exports to construct the DATEV export file. Therefore, first
open GnuCash and export your bookings and accounts via:

 - `File` &rarr; `Export` &rarr; `Export Transactions to CSV`
 - `File` &rarr; `Export` &rarr; `Export Account Tree to CSV`

Remember both filenames. Then, use GnuTev to convert your bookings:

```bash
$ python3 gnutev/main .../Gnucash-Accounts-Export.csv .../GnuCash-Transactions-Export.csv
```

That's it. If everything worked, your output should look similar to this:

```
Converting transactions from 2022-05-05 to 2023-06-09 (2 periods)…
 - Wrote output file 1/3 (2022-05-05 to 2022-12-31) containing 28 bookings to "output/EXTF_700_21_Buchungsstapel_2022.csv"
 - Wrote output file 2/3 (2023-01-01 to 2023-06-09) containing 147 bookings to "output/EXTF_700_21_Buchungsstapel_2023.csv"
2 DATEV-compatible files successfully created.
```

### Further customization
GnuTev offers some more arguments to customize your export. You can view it's usage
using `python3 gnutev/main.py --help`:

```
usage: gnucash/main.py [--financial-year-start FINANCIAL_YEAR_START] [--output-folder OUTPUT_FOLDER] [--title TITLE] accounts-csv-export transactions-csv-export

positional arguments:
  accounts-csv-export       The path to the Account Tree CSV file exported from GnuCash
  transactions-csv-export   The path to the Transactions CSV file exported from GnuCash

options:
  -h, --help                Show this help message and exit
  --financial-year-start FINANCIAL_YEAR_START
                            Start of the financial year in YYYY-MM-DD. If omitted, Jan 1 is
                            used for each year
  --output-folder OUTPUT_FOLDER
                            Path to the output folder to place DATEV files in. Default: 
                            current folder
  --title TITLE             Title of the exported DATEV files
```

## Using as a Python library
GnuTev can directly be used as a Python library – you can just import it. When doing so,
you're probably most interested in these objects:

```python3
import gnutev

# Allows writing data to a DATEV-compatible CSV file
help(gnutev.datev.BookingsCSVFile)

# Can parse GnuCash Transaction CSV exports
help(gnutev.gnucash.BookingsCSVFile)

# Can parse GnuCash Account Tree CSV exports
help(gnutev.gnucash.AccountsCSVFile)

# The main function (also used by the CLI) containing the necessary logic to convert
help(gnutev.convert_gnucash_to_datev)
```

Just use python's `help` built-in as indicated above or browse the source code in this
repo to learn more about these objects and their usage.

If you're using this as a library, I'd love if you let me know – I'm curious what uses 
it offers to creative developers.

## Contributing
I'm open to any kind of contribution – just create an issue and/or a pull request. 
In this corporate-dominated field FOSS enthusiasts have to stick together ;)

## Disclaimer
For my (rather simply) bookkeping, GnuTev has worked perfectly. However, I can 
imagine that issues can arise in more complex scenarios (i.e. taxes). Should
you come across any issues using GnuTev, don't hesitate to let me know so it can be
fixed.

Also note that I cannot and do not provide any kind of legal responsibility on the 
results obtained using GnuTev. This software is provided as-is and it is your own 
responsibility to thoroughly cross-check the results.
