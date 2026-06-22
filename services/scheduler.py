import re
import math
from datetime import datetime, timedelta, timezone

def parse_deadline_date(deadline_str: str, default_year: int = 2026) -> datetime:
    """
    Parses a deadline string into a timezone-aware datetime object.
    Supports ISO formats, DD-MM-YYYY, and relative month/day formats in English and Spanish.
    """
    if not deadline_str:
        return None
        
    s = deadline_str.strip().lower()
    
    # Map Spanish and English month names/abbreviations to month numbers
    months_map = {
        "jan": 1, "january": 1, "enero": 1, "ene": 1,
        "feb": 2, "february": 2, "febrero": 2,
        "mar": 3, "march": 3, "marzo": 3,
        "apr": 4, "april": 4, "abril": 4, "abr": 4,
        "may": 5, "mayo": 5,
        "jun": 6, "june": 6, "junio": 6, "juny": 6,
        "jul": 7, "july": 7, "julio": 7,
        "aug": 8, "august": 8, "agosto": 8, "ago": 8,
        "sep": 9, "september": 9, "septiembre": 9, "sept": 9,
        "oct": 10, "october": 10, "octubre": 10,
        "nov": 11, "november": 11, "noviembre": 11,
        "dec": 12, "december": 12, "diciembre": 12, "dic": 12
    }
    
    # 1. ISO YYYY-MM-DD
    iso_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if iso_match:
        return datetime(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)), tzinfo=timezone.utc)
        
    # 2. DD-MM-YYYY or DD/MM/YYYY
    dmy_match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
    if dmy_match:
        return datetime(int(dmy_match.group(3)), int(dmy_match.group(2)), int(dmy_match.group(1)), tzinfo=timezone.utc)

    # 3. Month name and day (e.g. "june 25", "25 de junio", "juny 25")
    found_month = None
    month_num = None
    for mname, mval in months_map.items():
        if re.search(r"\b" + re.escape(mname) + r"\b", s):
            if found_month is None or len(mname) > len(found_month):
                found_month = mname
                month_num = mval
                
    if month_num is not None:
        day_match = re.search(r"\b(\d{1,2})\b", s)
        if day_match:
            day_val = int(day_match.group(1))
            year_match = re.search(r"\b(20\d{2})\b", s)
            year_val = int(year_match.group(1)) if year_match else default_year
            return datetime(year_val, month_num, day_val, tzinfo=timezone.utc)
            
    return None

def parse_slot(slot_str: str) -> tuple:
    """
    Parses a single slot string (e.g. 'Monday-Friday 20:00-21:30' or 'Saturday 10:00-12:00').
    Returns a tuple: (list of days in lowercase, start_min, end_min)
    """
    slot_str = slot_str.lower().strip()
    if not slot_str:
        return [], 0, 0
        
    days = []
    weekdays_full = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    weekdays_short = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    
    # 1. Parse days
    # Check for a range (e.g. monday-friday, mon-fri)
    range_match = re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s*-\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b",
        slot_str
    )
    if range_match:
        start_day_str, end_day_str = range_match.groups()
        
        def get_full_day(d):
            if d in weekdays_full:
                return d
            idx = weekdays_short.index(d)
            return weekdays_full[idx]
            
        start_day = get_full_day(start_day_str)
        end_day = get_full_day(end_day_str)
        
        start_idx = weekdays_full.index(start_day)
        end_idx = weekdays_full.index(end_day)
        
        if start_idx <= end_idx:
            days = weekdays_full[start_idx : end_idx + 1]
        else:
            # e.g. Friday-Monday (wrap around)
            days = weekdays_full[start_idx:] + weekdays_full[:end_idx + 1]
    else:
        # Just check for individual day names
        for idx, day_full in enumerate(weekdays_full):
            day_short = weekdays_short[idx]
            if re.search(r"\b" + day_full + r"\b", slot_str) or re.search(r"\b" + day_short + r"\b", slot_str):
                days.append(day_full)
                
    # If no day was matched, check if "weekend" or "weekdays" is present
    if not days:
        if "weekend" in slot_str:
            days = ["saturday", "sunday"]
        elif "weekday" in slot_str:
            days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
            
    # 2. Parse time range
    time_match = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", slot_str)
    if time_match:
        sh, sm, eh, em = map(int, time_match.groups())
        start_min = sh * 60 + sm
        end_min = eh * 60 + em
    else:
        # Default start and end based on keywords
        if "afternoon" in slot_str:
            start_min = 14 * 60
            end_min = 16 * 60
        elif "morning" in slot_str:
            start_min = 10 * 60
            end_min = 12 * 60
        else:
            start_min = 19 * 60
            end_min = 20 * 60 + 30  # 19:00 - 20:30
        
    return days, start_min, end_min

def generate_schedule(tasks: list, availability: str, sessions_pref: str, deadline: str = None) -> list:
    """
    Distributes the given list of tasks across availability windows to generate
    concrete study/work sessions, strictly honoring the target completion deadline.
    
    Returns a list of dictionaries, each containing:
      - week: Integer
      - day: String (e.g., 'Monday')
      - time: String (e.g., '20:00-21:30')
      - task: String
    """
    schedule = []
    if not tasks:
        return schedule

    # Monday, Jun 22, 2026 is our reference date for scheduling offsets
    base_date = datetime(2026, 6, 22, tzinfo=timezone.utc)

    # 1. Parse availability and sessions_pref into structured slots
    slots = []
    for input_str in [availability, sessions_pref]:
        if not input_str:
            continue
        
        # Smart splitting: split by semicolon if present, otherwise split by comma with time-based merging
        if ";" in input_str:
            parts = [p.strip() for p in input_str.split(";") if p.strip()]
        else:
            raw_parts = [p.strip() for p in input_str.split(",") if p.strip()]
            parts = []
            current_part = ""
            for p in raw_parts:
                if current_part:
                    current_part += ", " + p
                else:
                    current_part = p
                has_time = re.search(r"\d{1,2}:\d{2}", current_part) or "morning" in current_part or "afternoon" in current_part or "evening" in current_part
                if has_time:
                    parts.append(current_part)
                    current_part = ""
            if current_part:
                parts.append(current_part)

        for part in parts:
            part = part.strip()
            if part:
                days, start_min, end_min = parse_slot(part)
                if days:
                    slots.append({
                        "days": days,
                        "start_min": start_min,
                        "end_min": end_min
                    })

    # Fallback to default slots if none could be parsed
    if not slots:
        slots.append({
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_min": 19 * 60,
            "end_min": 20 * 60 + 30
        })
        slots.append({
            "days": ["saturday"],
            "start_min": 10 * 60,
            "end_min": 12 * 60
        })

    # Collect all day names that have availability
    all_avail_days = set()
    for s in slots:
        all_avail_days.update(s["days"])

    # 2. Determine target dates based on deadline
    deadline_date = parse_deadline_date(deadline)
    
    # Generate list of allowed dates
    allowed_dates = []
    if deadline_date and deadline_date >= base_date:
        max_days = (deadline_date - base_date).days
        for d in range(max_days + 1):
            curr_date = base_date + timedelta(days=d)
            day_name = curr_date.strftime("%A").lower()
            if day_name in all_avail_days:
                allowed_dates.append(curr_date)
    
    # Fallback to a default 4-week window if no dates are allowed (e.g. deadline missing or past)
    if not allowed_dates:
        for d in range(28):
            curr_date = base_date + timedelta(days=d)
            day_name = curr_date.strftime("%A").lower()
            if day_name in all_avail_days:
                allowed_dates.append(curr_date)

    # Sort allowed dates chronologically
    allowed_dates.sort()

    # 3. Distribute tasks date-by-date (preserving block-by-block chronological grouping)
    num_dates = len(allowed_dates)
    tasks_per_day = math.ceil(len(tasks) / num_dates) if num_dates > 0 else 1
    
    day_sessions_count = {}  # date_str -> count of tasks scheduled on it

    for i, task in enumerate(tasks):
        # Determine the target date index
        date_idx = i // tasks_per_day
        if date_idx >= len(allowed_dates):
            date_idx = len(allowed_dates) - 1 # Fallback to the last available day
        
        target_date = allowed_dates[date_idx]
        date_str = target_date.strftime("%Y-%m-%d")
        day_name_lower = target_date.strftime("%A").lower()
        
        # Get session index on this day
        session_seq = day_sessions_count.get(date_str, 0)
        day_sessions_count[date_str] = session_seq + 1
        
        # Find all slots that apply to this day of the week
        matching_slots = [s for s in slots if day_name_lower in s["days"]]
        if not matching_slots:
            # Fallback if no matching slot found
            matching_slots = [{"start_min": 19 * 60, "end_min": 20 * 60 + 30}]
            
        # Select the slot corresponding to this session sequence on this day
        slot_idx = session_seq % len(matching_slots)
        slot = matching_slots[slot_idx]
        
        start_min = slot["start_min"]
        end_min = slot["end_min"]
        duration = end_min - start_min
        if duration <= 0:
            duration = 90
            
        # Calculate how many times we've wrapped around the slots list on this day
        shift_multiplier = session_seq // len(matching_slots)
        
        # Calculate time range
        s_min = start_min + shift_multiplier * duration
        e_min = s_min + duration
            
        # Adjust for midnight rollover (if s_min is 1440 minutes or more)
        days_shift = s_min // 1440
        session_date = target_date + timedelta(days=days_shift)
        
        s_min_day = s_min % 1440
        e_min_day = e_min % 1440
        
        if e_min_day == s_min_day:
            e_min_day = s_min_day + duration
            
        start_time_str = f"{s_min_day // 60:02d}:{s_min_day % 60:02d}"
        end_time_str = f"{e_min_day // 60:02d}:{e_min_day % 60:02d}"
        time_range_str = f"{start_time_str}-{end_time_str}"
        
        # Calculate week number and day name relative to actual session_date
        days_diff = (session_date - base_date).days
        week_num = (days_diff // 7) + 1
        day_name = session_date.strftime("%A")
        
        schedule.append({
            "week": week_num,
            "day": day_name,
            "time": time_range_str,
            "task": task
        })
        
    return schedule


