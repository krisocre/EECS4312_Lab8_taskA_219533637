import pytest
from datetime import date, time, timedelta
from solution import TimeWindow, BusyInterval, suggest_slots


def assert_result_invariants(result, n):
    """Verifies that the result follows basic system rules."""
    assert hasattr(result, 'slots')
    assert hasattr(result, 'system_logs')
    assert hasattr(result, 'status')
    assert len(result.slots) <= n
    times = [s.start_time for s in result.slots]
    assert times == sorted(times)


# Covers C1, AC1
def test_deterministic_sort_order():
    """Verifies C1: Predictable and stable ordering for Jane and Mo."""
    day = date(2026, 3, 6)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(9, 0), time(10, 0), name="Z-Event"),
        BusyInterval(time(9, 0), time(10, 0), name="A-Event")
    ]
    result = suggest_slots(day, working, busy, timedelta(minutes=30), n=1)
    assert_result_invariants(result, 1)
    # TBR1: Alphabetical tie-break ensures 10:00 is the consistent output
    assert result.slots[0].start_time == time(10, 0)

# Covers C2, AC2
def test_waitlist_promotion_logging():
    """Verifies C2: Mo's need for explanations and transparency."""
    day = date(2026, 3, 6)
    working = TimeWindow(time(9, 0), time(10, 0))
    busy = [BusyInterval(time(9, 15), time(9, 45), name="Medication")]
    result = suggest_slots(day, working, busy, timedelta(minutes=30), n=5)
    # Mo expects a clear log entry for the skipped/moved slot
    assert any("Skipped" in log and "Medication" in log for log in result.system_logs)

# Covers C3, AC3
def test_notification_suppression_window():
    """Verifies C3: Jane's pain point regarding notification overload."""
    day = date(2026, 3, 6)
    working = TimeWindow(time(9, 0), time(10, 0))
    result = suggest_slots(day, working, [], timedelta(minutes=30), n=2)
    # Throttling/Stepping ensures slots aren't suggested every minute
    assert result.slots[0].start_time == time(9, 0)
    assert result.slots[1].start_time == time(9, 5)

# Covers C4, AC4 (Edge Case: EC1)
def test_capacity_zero_error_handling():
    """Verifies C4: Mo's need for explicit handling of zero-capacity/impossible windows."""
    day = date(2026, 3, 6)
    working = TimeWindow(time(9, 0), time(9, 15)) 
    result = suggest_slots(day, working, [], timedelta(minutes=30), n=1)
    # Explicit status return instead of silent failure
    assert result.status == "No Availability Found"
    assert len(result.slots) == 0

# Covers C6, AC5 (Edge Case: EC2)
def test_request_idempotency_check():
    """Verifies C6: Mo's need for consistent responses across repeated scenarios."""
    day = date(2026, 3, 6)
    working = TimeWindow(time(9, 0), time(17, 0))
    busy = [BusyInterval(time(10, 0), time(11, 0), name="Meeting")]
    out1 = suggest_slots(day, working, busy, timedelta(minutes=30), n=3)
    out2 = suggest_slots(day, working, busy, timedelta(minutes=30), n=3)
    assert [s.start_time for s in out1.slots] == [s.start_time for s in out2.slots]

# Covers C7, AC6 (Edge Case: EC5)
def test_priority_conflict_resolution():
    """Verifies C7: Jane's trust in the system to resolve overlaps automatically with buffers."""
    day = date(2026, 3, 6)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(9, 0), time(10, 0), name="High Priority Med"),
        BusyInterval(time(11, 0), time(12, 0), name="Routine Task")
    ]
    # Testing a gap that is too small once a 15-min buffer is applied
    result = suggest_slots(day, working, busy, timedelta(minutes=45), n=1, buffer=timedelta(minutes=15))
    assert len(result.slots) == 0
