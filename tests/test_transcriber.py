import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transcriber import format_time


def test_format_time_under_one_hour():
    assert format_time(0) == "00:00.000"
    assert format_time(65.5) == "01:05.500"


def test_format_time_with_hours():
    assert format_time(3661.25) == "01:01:01.250"
