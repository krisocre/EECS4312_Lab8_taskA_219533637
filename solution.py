## Student Name: MHD-Oubai Al-khimi
## Student ID:219 533 637

"""
Task A: Appointment Timeslot Recommender (Stub)

In this lab, you will design and implement an Appointment Slot Recommender using an LLM assistant
as your primary programming collaborator.

You are asked to implement a Python module that recommends available meeting slots within a
defined working window.

The system must:
  • Accept working hours (start and end time).
  • Accept a list of existing busy intervals.
  • Accept a required meeting duration.
  • Accept an optional buffer time between meetings.
  • Optionally restrict suggestions to a candidate time window.
  • Return chronologically ordered appointment slots that satisfy all constraints.

The system must ensure that:
  • Suggested slots fall within working hours.
  • Suggested slots do not overlap busy intervals.
  • Buffer time is respected when evaluating availability.
  • Output ordering is deterministic under identical inputs.

The module must preserve the following invariants:
  • Returned slots must be at least as long as the required duration.
  • No returned slot may violate buffer constraints.
  • The returned list must reflect the current system state.

The system must correctly handle non-trivial scenarios such as:
  • Adjacent busy intervals.
  • Very small gaps between meetings.
  • Buffers eliminating otherwise valid availability.
  • Overlapping or unsorted busy intervals.
  • A meeting duration longer than any available gap.
  • No availability within the working window.

Output:
  The output consists of the next N valid appointment suggestions in chronological order.
  Behavior must be deterministic under ties (if any).

See the lab handout for full requirements.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple


# ---------------- Data Models ----------------
from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional

@dataclass(frozen=True)
class TimeWindow:
    start: time
    end: time

@dataclass(frozen=True)
class BusyInterval:
    start: time
    end: time

@dataclass(frozen=True)
class Slot:
    start_time: time

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:
    
    if n <= 0:
        return []

    # 1. Determine the effective search boundaries
    start_limit = working_hours.start
    end_limit = working_hours.end
    
    if candidate_window:
        start_limit = max(start_limit, candidate_window.start)
        end_limit = min(end_limit, candidate_window.end)
    
    if start_limit >= end_limit:
        return []

    # Convert to datetime for easier math
    search_start = datetime.combine(day, start_limit)
    search_end = datetime.combine(day, end_limit)

    # 2. Merge and sort busy intervals
    # We also treat the time before and after the working window as "busy"
    sorted_busy = sorted(busy_intervals, key=lambda x: x.start)
    merged_busy: List[Tuple[datetime, datetime]] = []
    
    for interval in sorted_busy:
        b_start = datetime.combine(day, interval.start)
        b_end = datetime.combine(day, interval.end)
        
        if not merged_busy or b_start > merged_busy[-1][1]:
            merged_busy.append((b_start, b_end))
        else:
            # Overlap or adjacency: extend the last interval
            merged_busy[-1] = (merged_busy[-1][0], max(merged_busy[-1][1], b_end))

    # 3. Sliding Window Search
    # We use a 5-minute step for suggestions, but this can be adjusted
    step = timedelta(minutes=5)
    suggestions = []
    current_time = search_start

    while current_time + duration <= search_end and len(suggestions) < n:
        slot_start = current_time
        slot_end = current_time + duration
        
        is_valid = True
        for b_start, b_end in merged_busy:
            # A slot is invalid if it overlaps a busy interval OR 
            # if it violates the buffer zones around that interval.
            # Effectively: Busy zone is [b_start - buffer, b_end + buffer]
            effective_b_start = b_start - buffer
            effective_b_end = b_end + buffer
            
            # Check overlap: (StartA < EndB) and (EndA > StartB)
            if slot_start < effective_b_end and slot_end > effective_b_start:
                is_valid = False
                # Optimization: Jump to the end of the busy block's influence
                current_time = effective_b_end
                break
        
        if is_valid:
            suggestions.append(Slot(start_time=slot_start.time()))
            current_time += step
        else:
            # If invalid and we didn't already jump, move by the step
            if current_time == slot_start:
                current_time += step

    return suggestions
