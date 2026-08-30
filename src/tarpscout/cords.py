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
    ordered_cords = tuple(sorted(cords, key=lambda cord: (cord.length, cord.id)))
    empty: tuple[CordUse | None, ...] = (None,) * len(needs)
    states: dict[int, tuple[float, tuple[CordUse | None, ...]]] = {0: (0.0, empty)}

    for cord in ordered_cords:
        updated = states.copy()
        for mask, (spare, uses) in states.items():
            for need_index, need in enumerate(needs):
                bit = 1 << need_index
                if mask & bit:
                    continue
                if cord.length + 1e-9 < need.required_length:
                    continue
                use = CordUse(
                    need.id,
                    cord.id,
                    need.required_length,
                    cord.length,
                    round(cord.length - need.required_length, 9),
                )
                candidate_uses = (*uses[:need_index], use, *uses[need_index + 1 :])
                candidate = (round(spare + use.spare_length, 9), candidate_uses)
                candidate_key = (
                    candidate[0],
                    tuple(item.cord_id if item is not None else "" for item in candidate_uses),
                )
                current = updated.get(mask | bit)
                if current is not None:
                    current_key = (
                        current[0],
                        tuple(item.cord_id if item is not None else "" for item in current[1]),
                    )
                    if current_key <= candidate_key:
                        continue
                updated[mask | bit] = candidate
        states = updated

    result = states.get((1 << len(needs)) - 1)
    if result is None:
        return None
    return tuple(use for use in result[1] if use is not None)
