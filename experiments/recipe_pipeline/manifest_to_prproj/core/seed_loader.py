"""Seed prproj loader + IdFactory.

The writer is a template-mutation pipeline (not a synthesis pipeline). It
loads SEQ_FLAT.prproj as a seed — full Premiere boilerplate + 1 working V1
clip in an empty Sequence 01 — then mutates it. To avoid ObjectID collisions
with the seed, the writer scans the seed's max ObjectID + every ObjectUID
already in use, then bootstraps an IdFactory at max+1.

This module has no dependencies on other writer modules.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


# Anchored at the experiments root so both module and script invocations
# resolve the same paths.
REPO_ROOT = Path(__file__).resolve().parents[4]
SEED_PRPROJ = REPO_ROOT / "experiments" / "PREMIERE PROJECTS" / "TESTS" / "SEQ_FLAT.prproj"
OUTPUTS_ROOT = REPO_ROOT / "experiments" / "PREMIERE PROJECTS" / "OUTPUTS"


@dataclass
class IdFactory:
    """Vends fresh ObjectIDs (numeric strings) and ObjectUIDs (uuid strings).

    Bootstrap with `next_object_id = max_existing + 1` and
    `used_uids = set(every UID already in the seed)` so collisions are
    impossible. Numeric ObjectIDs are scope-local in Premiere's schema, but
    in practice the writer treats them as document-globally unique — that's
    simpler and the seed only has ~60 of them.
    """

    next_object_id: int = 1
    used_uids: set = field(default_factory=set)

    def fresh_id(self) -> str:
        i = self.next_object_id
        self.next_object_id += 1
        return str(i)

    def fresh_uid(self) -> str:
        while True:
            u = str(uuid.uuid4())
            if u not in self.used_uids:
                self.used_uids.add(u)
                return u


def parse_xml(xml_bytes: bytes) -> ET.ElementTree:
    return ET.ElementTree(ET.fromstring(xml_bytes))


def find_max_object_id(root: ET.Element) -> int:
    mx = 0
    for el in root.iter():
        oid = el.get("ObjectID")
        if oid and oid.isdigit():
            mx = max(mx, int(oid))
    return mx


def collect_used_uids(root: ET.Element) -> set[str]:
    uids = set()
    for el in root.iter():
        u = el.get("ObjectUID")
        if u:
            uids.add(u)
    return uids


def find_premiere_data(tree: ET.ElementTree) -> ET.Element:
    """SEQ_FLAT root is <PremiereData Version="3">. Return that element."""
    return tree.getroot()
