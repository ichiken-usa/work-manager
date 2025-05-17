from datetime import datetime, time, date
from typing import Any, Dict, List, Optional

def parse_time_str(tstr: Optional[str]) -> time:
    """"HH:MM"形式の文字列をtime型に変換。失敗時は00:00を返す。"""
    if not tstr:
        return time(0, 0)
    try:
        return datetime.strptime(tstr, "%H:%M").time()
    except Exception:
        return time(0, 0)