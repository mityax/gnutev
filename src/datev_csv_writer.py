from _decimal import Decimal
from typing import Iterable, Any


class DatevCSVWriter:
    """
    Drop-in replacement for the builtin `csv.writer` since it doesn't support formatting
    numbers using a different fraction separator (",") without quoting them.
    """

    def __init__(self, outfd: 'SupportsWrite[str]', quotechar='"', delimiter=';', fraction_separator=",", newline="\r\n"):
        self.outfd = outfd
        self.quotechar = quotechar
        self.delimiter = delimiter
        self.fraction_separator = fraction_separator
        self.newline = newline

    def writerow(self, row: Iterable[Any]):
        strings = []

        for el in row:
            string = str(el) if el is not None else ""
            string = string.replace(self.quotechar, 2*self.quotechar)  # double any quote chars

            # Replace fraction separator in floats and Decimals:
            if isinstance(el, float) or isinstance(el, Decimal):
                string = string.replace(".", self.fraction_separator)

            # Quote all non-numerics:
            if not isinstance(el, float) and not isinstance(el, Decimal) and not isinstance(el, int):
                string = self.quotechar + string + self.quotechar

            strings.append(string)

        self.outfd.write(self.delimiter.join(strings) + self.newline)
