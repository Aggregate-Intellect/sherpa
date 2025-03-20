from __future__ import annotations

import csv
import os
from collections import defaultdict
from enum import Enum

from typing import Dict, List, Union


class _CodesColumn(Enum):
    ID = "Id"
    PART2B = "Part2b"
    PART2T = "Part2t"
    PART1 = "Part1"
    SCOPE = "Scope"
    TYPE = "Language_Type"
    REF_NAME = "Ref_Name"
    COMMENT = "Comment"


class _NameIndexColumn(Enum):
    ID = "Id"
    PRINT_NAME = "Print_Name"
    INVERTED_NAME = "Inverted_Name"


class _RetirementsColumn(Enum):
    ID = "Id"
    REF_NAME = "Ref_Name"
    RET_REASON = "Ret_Reason"
    CHANGE_TO = "Change_To"
    REMEDY = "Ret_Remedy"
    EFFECTIVE = "Effective"


class _MacrolanguagesColumn(Enum):
    ID = "I_Id"
    MID = "M_Id"
    STATUS = "I_Status"


_COLUMN_TYPE = Union[
    _CodesColumn, _NameIndexColumn, _RetirementsColumn, _MacrolanguagesColumn
]
_ROW_TYPE = Dict[_COLUMN_TYPE, str]


class _Table(Enum):
    CODES = _CodesColumn
    NAME_INDEX = _NameIndexColumn
    RETIREMENTS = _RetirementsColumn
    MACROLANGUAGES = _MacrolanguagesColumn


_THIS_DIR = os.path.dirname(__file__)
_DATA_TSV_PATHS = {
    _Table.CODES: os.path.join(_THIS_DIR, "iso-639-3.tab"),
    _Table.NAME_INDEX: os.path.join(_THIS_DIR, "iso-639-3_Name_Index.tab"),
    _Table.MACROLANGUAGES: os.path.join(_THIS_DIR, "iso-639-3-macrolanguages.tab"),
    _Table.RETIREMENTS: os.path.join(_THIS_DIR, "iso-639-3_Retirements.tab"),
}


def _load_tsv(table: _Table) -> List[_ROW_TYPE]:
    column = table.value
    with open(_DATA_TSV_PATHS[table], encoding="utf-8", newline="") as tsv_file:
        tsv_reader = csv.DictReader(tsv_file, delimiter="\t")
        return [{column(k): v for k, v in row.items()} for row in tsv_reader]


_PART3_TO_CODES: Dict[str, _ROW_TYPE] = {
    row[_CodesColumn.ID]: row for row in _load_tsv(_Table.CODES)
}

_part3_to_name_index: defaultdict[str, List[_ROW_TYPE]] = defaultdict(list)
for row in _load_tsv(_Table.NAME_INDEX):
    _part3_to_name_index[row[_NameIndexColumn.ID]].append(row)
_PART3_TO_NAME_INDEX: Dict[str, List[_ROW_TYPE]] = dict(_part3_to_name_index)

_PART3_TO_RETIREMENTS: Dict[str, _ROW_TYPE] = {
    row[_RetirementsColumn.ID]: row for row in _load_tsv(_Table.RETIREMENTS)
}
_PART3_TO_MACROLANGUAGES: Dict[str, _ROW_TYPE] = {
    row[_MacrolanguagesColumn.ID]: row for row in _load_tsv(_Table.MACROLANGUAGES)
}

_PART2B_TO_PART3: Dict[str, str] = {
    row[_CodesColumn.PART2B]: part3
    for part3, row in _PART3_TO_CODES.items()
    if row[_CodesColumn.PART2B]
}
_PART2T_TO_PART3: Dict[str, str] = {
    row[_CodesColumn.PART2T]: part3
    for part3, row in _PART3_TO_CODES.items()
    if row[_CodesColumn.PART2T]
}
_PART1_TO_PART3: Dict[str, str] = {
    row[_CodesColumn.PART1]: part3
    for part3, row in _PART3_TO_CODES.items()
    if row[_CodesColumn.PART1]
}
_REF_NAME_TO_PART3: Dict[str, str] = {
    row[_CodesColumn.REF_NAME]: part3
    for part3, row in _PART3_TO_CODES.items()
    if row[_CodesColumn.REF_NAME]
}
_PRINT_NAME_TO_PART3: Dict[str, str] = {
    row[_NameIndexColumn.PRINT_NAME]: part3
    for part3, rows in _PART3_TO_NAME_INDEX.items()
    for row in rows
    if row[_NameIndexColumn.PRINT_NAME]
}
_INVERTED_NAME_TO_PART3: Dict[str, str] = {
    row[_NameIndexColumn.INVERTED_NAME]: part3
    for part3, rows in _PART3_TO_NAME_INDEX.items()
    for row in rows
    if row[_NameIndexColumn.INVERTED_NAME]
}
