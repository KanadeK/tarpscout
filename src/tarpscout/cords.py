"""Exact assignment of reusable cord segments to line requirements."""

from __future__ import annotations

from dataclasses import dataclass

from tarpscout.models import Cord


@dataclass(frozen=True, slots=True)
class CordNeed:
    id: str
    required_length: float


@dataclass(frozen=True, slots=True)
class CordUse:
    need_id: str
    cord_id: str
    required_length: float
    cord_length: float
    spare_length: float


def assign_cords(
    needs: tuple[CordNeed, ...], cords: tuple[Cord, ...]
) -> tuple[CordUse, ...] | None:
    ordered_needs = tuple(
        sorted(enumerate(needs), key=lambda item: (-item[1].required_length, item[1].id))
    )
    ordered_cords = tuple(sorted(cords, key=lambda cord: (cord.length, cord.id)))
    best_key: tuple[float, tuple[str, ...]] | None = None
    best_by_index: dict[int, CordUse] | None = None

    def search(position: int, available: tuple[Cord, ...], chosen: dict[int, CordUse]) -> None:
        nonlocal best_key, best_by_index
        if position == len(ordered_needs):
            uses = tuple(chosen[index] for index in range(len(needs)))
            key = (
                round(sum(use.spare_length for use in uses), 9),
                tuple(use.cord_id for use in uses),
            )
            if best_key is None or key < best_key:
                best_key = key
                best_by_index = chosen.copy()
            return
        original_index, need = ordered_needs[position]
        for cord_index, cord in enumerate(available):
            if cord.length + 1e-9 < need.required_length:
                continue
            chosen[original_index] = CordUse(
                need.id,
                cord.id,
                need.required_length,
                cord.length,
                round(cord.length - need.required_length, 9),
            )
            search(position + 1, available[:cord_index] + available[cord_index + 1 :], chosen)
            del chosen[original_index]

    search(0, ordered_cords, {})
    if best_by_index is None:
        return None
    return tuple(best_by_index[index] for index in range(len(needs)))
