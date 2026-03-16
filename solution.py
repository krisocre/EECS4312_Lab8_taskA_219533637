## Student Name: MHD-Oubai Al-khimi
## Student ID:219 533 637
# solution.py
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class TimeWindow:
    start: time
    end: time

@dataclass(frozen=True)
class BusyInterval:
    start: time
    end: time
    name: str = "Busy" 

@dataclass(frozen=True)
class Slot:
    start_time: time
    reason: str = "Available slot" # Satisfies C2/FR4 (Transparency)

@dataclass
class RecommendationResult:
    slots: List[Slot]
    system_logs: List[str] # Satisfies C2/C8 (The "Review Log" for Mo)
    status: str = "Success" # Satisfies C4 (Explicit status instead of silent failure)

# ---------------- Implementation ----------------

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> RecommendationResult:
    
    logs = []
    
    if n <= 0:
        return RecommendationResult([], ["Requested zero or negative slots."], status="Error: Invalid Input")

    # 1. Determine the effective search boundaries
    start_limit = working_hours.start
    end_limit = working_hours.end
    
    if candidate_window:
        start_limit = max(start_limit, candidate_window.start)
        end_limit = min(end_limit, candidate_window.end)
        logs.append(f"Search restricted to candidate window: {start_limit} - {end_limit}")
    
    if start_limit >= end_limit:
        return RecommendationResult([], ["Candidate window outside of working hours."], status="Capacity Exceeded")

    search_start = datetime.combine(day, start_limit)
    search_end = datetime.combine(day, end_limit)

    # 2. Merge and sort busy intervals (Deterministic - Satisfies C1/Mo's Need)
    # TBR1: Alphabetical tie-break if times are identical
    sorted_busy = sorted(busy_intervals, key=lambda x: (x.start, x.name))
    merged_busy: List[Tuple[datetime, datetime, str]] = []
    
    for interval in sorted_busy:
        b_start = datetime.combine(day, interval.start)
        b_end = datetime.combine(day, interval.end)
        
        if not merged_busy or b_start > merged_busy[-1][1]:
            merged_busy.append((b_start, b_end, interval.name))
        else:
            # Overlap handling
            new_end = max(merged_busy[-1][1], b_end)
            merged_busy[-1] = (merged_busy[-1][0], new_end, f"Merged: {merged_busy[-1][2]} & {interval.name}")

    # 3. Sliding Window Search
    # C3/Jane: 5-minute step prevents "notification flooding" of near-identical slots
    step = timedelta(minutes=5)
    suggestions = []
    current_time = search_start

    while current_time + duration <= search_end and len(suggestions) < n:
        slot_start = current_time
        slot_end = current_time + duration
        
        is_valid = True
        for b_start, b_end, b_name in merged_busy:
            # C6/C7: Effective busy zone includes buffer
            effective_b_start = b_start - buffer
            effective_b_end = b_end + buffer
            
            if slot_start < effective_b_end and slot_end > effective_b_start:
                is_valid = False
                logs.append(f"Skipped {slot_start.time()} due to conflict with {b_name} (Buffer: {buffer})")
                current_time = effective_b_end # Optimization: Jump past conflict
                break
        
        if is_valid:
            reason = "Earliest available" if not suggestions else "Next available after 5m step"
            suggestions.append(Slot(start_time=slot_start.time(), reason=reason))
            current_time += step
        else:
            if current_time == slot_start:
                current_time += step

    # Final Persona Check: No silent failures (C4)
    if not suggestions:
        status = "No Availability Found"
        logs.append("The schedule is fully constrained; no valid slots meet duration/buffer requirements.")
    else:
        status = "Success"

    return RecommendationResult(slots=suggestions, system_logs=logs, status=status)
