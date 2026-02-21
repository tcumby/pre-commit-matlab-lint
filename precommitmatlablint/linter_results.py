import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class LinterRecord:
    id: str = ""
    message: str = ""
    line: int = 0
    columns: List[int] = field(default_factory=list)

    def __str__(self):
        if len(self.columns) == 2:
            return f"Line {self.line} (Columns {self.columns[0]}-{self.columns[1]}): {self.id}: {self.message}"
        elif len(self.columns) == 1:
            return f"Line {self.line} (Column {self.columns[0]}): {self.id}: {self.message}"
        else:
            return f"Line {self.line}: {self.id}: {self.message}"

    @classmethod
    def from_mlint(cls, mlint_message: str) -> "LinterRecord":
        mlint_elements = mlint_message.split(":")

        line_and_column = mlint_elements[0]
        id: str = mlint_elements[1].strip()
        message: str = mlint_elements[2].strip()
        match = re.match(
            pattern=r".*L\s*(?P<line>\d+)\s*\(C\s*(?P<column_min>\d+)(\-(?P<column_max>\d+)\))?",
            string=line_and_column,
        )
        line: int = 0
        columns: List[int] = []
        if match:
            line = int(match.group("line"))

            column_min = match.group("column_min")
            columns.append(int(column_min))

            column_max = match.group("column_max")
            if column_max:
                columns.append(int(column_max))

        return LinterRecord(id=id, message=message, line=line, columns=columns)


@dataclass(frozen=True)
class LinterReport:
    source_file: Path = Path()
    records: List[LinterRecord] = field(default_factory=list)

    def has_records(self) -> bool:
        return len(self.records) > 0
