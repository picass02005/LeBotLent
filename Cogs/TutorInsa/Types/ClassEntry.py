# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

from typing import List, Dict


class ClassEntry:
    name: str
    year: int
    department: str
    po: str
    speciality: str
    next: List[str]
    similar: List[str]

    def __init__(self, d: Dict[str, str | int | List[str] | None]) -> None:
        self.name = d["Name"]
        self.year = d["Year"]
        self.department = d["Department"]
        self.po = d["PO"]
        self.speciality = d["Speciality"]
        self.next = d["Next"]
        self.similar = d["Similar"]
