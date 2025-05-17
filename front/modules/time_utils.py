from datetime import datetime, time
from typing import Optional

def parse_time_str(tstr: Optional[str]) -> time:
    """"HH:MM"形式の文字列をtime型に変換。失敗時は00:00を返す。"""
    if not tstr:
        return time(0, 0)
    try:
        return datetime.strptime(tstr, "%H:%M").time()
    except Exception:
        return time(0, 0)
    
# interruptionsを文字列（"HH:MM"）に変換
def serialize_interruptions(inter_list):
    result = []
    for i in inter_list:
        result.append({
            "start": i["start"].strftime("%H:%M") if isinstance(i["start"], datetime.time) else i["start"],
            "end": i["end"].strftime("%H:%M") if isinstance(i["end"], datetime.time) else i["end"],
        })
    return result
