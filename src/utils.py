import datetime as dt
import re
from typing import Generator, Tuple, Any

AnyDateRepresentation = dt.date | str | int | float


def parse_any_date(x: str | float | int | dt.date) -> dt.date:
    if isinstance(x, dt.date):
        return x
    elif isinstance(x, str):
        if '-' in x:  # prob. "2022-08-15"
            y, m, d = x.split("-")
            return dt.date(int(y), int(m), int(d))
        elif m := re.match(r"(\d\d)/(\d\d)/(\d\d)", x):  # MM/DD/YY
            return dt.date(2000 + int(m.group(3)), int(m.group(1)), int(m.group(2)))
        elif m := re.match(r"(\d\d)/(\d\d)/(\d\d\d\d)", x):  # MM/DD/YYYY
            return dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        elif m := re.match(r"(\d\d)\.(\d\d)\.(\d\d)", x):  # DD.MM.YY
            return dt.date(2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))
        elif m := re.match(r"(\d\d)\.(\d\d)\.(\d\d\d\d)", x):  # DD.MM.YYYY
            return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        elif x.isnumeric() and len(x) == 8:  # YYYYMMDD
            return dt.date(int(x[:4]), int(x[4:6]), int(x[6:8]))
        raise ValueError(f"Unknown date format: {x}")
    elif isinstance(x, int) or isinstance(x, float):
        return dt.date.fromtimestamp(x)


def yearly_split(end_date: dt.date, start_date: dt.date) -> Generator[Tuple[dt.date, dt.date], None, None]:
    if not start_date < end_date:
        raise ValueError(f"Start date must be before end date: start={start_date.isoformat()} is not "
                         f"before end={end_date.isoformat()}")

    prev = start_date

    for year in range(start_date.year, end_date.year):
        yield prev, dt.date(year, 12, 31)
        prev = dt.date(year + 1, 1, 1)

    yield prev, end_date


def truncate_string(string: str, length: int, end='...') -> str:
    if len(string) <= length:
        return string
    else:
        return string[:length - len(end)] + end
