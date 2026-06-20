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

    # 1. Parse availability to find available days of the week (lowercase list)
    avail_lower = availability.lower()
    days_to_schedule = []
    
    if "monday-friday" in avail_lower or "mon-fri" in avail_lower:
        days_to_schedule.extend(["monday", "tuesday", "wednesday", "thursday", "friday"])
    else:
        if "monday" in avail_lower or "mon" in avail_lower:
            days_to_schedule.append("monday")
        if "tuesday" in avail_lower or "tue" in avail_lower:
            days_to_schedule.append("tuesday")
        if "wednesday" in avail_lower or "wed" in avail_lower:
            days_to_schedule.append("wednesday")
        if "thursday" in avail_lower or "thu" in avail_lower:
            days_to_schedule.append("thursday")
        if "friday" in avail_lower or "fri" in avail_lower:
            days_to_schedule.append("friday")

    if "saturday" in avail_lower or "sat" in avail_lower:
        days_to_schedule.append("saturday")
    if "sunday" in avail_lower or "sun" in avail_lower:
        days_to_schedule.append("sunday")

    if not days_to_schedule:
        days_to_schedule = ["monday", "wednesday", "friday", "saturday"]

    # 2. Parse time window from availability
    default_start, default_end = "19:00", "20:30"
    time_match = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", availability)
    if time_match:
        sh, sm, eh, em = map(int, time_match.groups())
        start_min = sh * 60 + sm
        end_min = eh * 60 + em
        duration = end_min - start_min
    else:
        sh, sm = map(int, default_start.split(":"))
        eh, em = map(int, default_end.split(":"))
        start_min = sh * 60 + sm
        duration = 90  # 1.5 hours

    # Parse weekend time preference if weekend days are used
    pref_time_match = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", sessions_pref)
    if pref_time_match:
        psh, psm, peh, pem = map(int, pref_time_match.groups())
        pref_start_min = psh * 60 + psm
        pref_duration = (peh * 60 + pem) - pref_start_min
    else:
        pref_start_min = 10 * 60  # 10:00 morning default
        if "afternoon" in sessions_pref.lower():
            pref_start_min = 14 * 60  # 14:00 afternoon
        pref_duration = 120  # 2 hours default

    # 3. Determine target dates based on deadline
    deadline_date = parse_deadline_date(deadline)
    
    # Generate list of allowed dates
    allowed_dates = []
    if deadline_date and deadline_date >= base_date:
        max_days = (deadline_date - base_date).days
        for d in range(max_days + 1):
            curr_date = base_date + timedelta(days=d)
            day_name = curr_date.strftime("%A").lower()
            if day_name in days_to_schedule:
                allowed_dates.append(curr_date)
    
    # If no allowed dates found (e.g. deadline is missing or too early), fallback to default weeks
    if not allowed_dates:
        # Default fallback: generate 4 weeks of allowed weekdays
        for w in range(4):
            for dname in days_to_schedule:
                day_offsets = {
                    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                    "friday": 4, "saturday": 5, "sunday": 6
                }
                offset = day_offsets.get(dname, 0)
                allowed_dates.append(base_date + timedelta(days=w * 7 + offset))

    # 4. Distribute tasks chronologically across the allowed dates
    num_dates = len(allowed_dates)
    tasks_per_day = math.ceil(len(tasks) / num_dates) if num_dates > 0 else 1
    
    day_sessions_count = {}  # date_str -> count of tasks scheduled on it

    for i, task in enumerate(tasks):
        # Find the date index
        date_idx = i // tasks_per_day
        if date_idx >= len(allowed_dates):
            date_idx = len(allowed_dates) - 1 # Fallback to the last available day
        
        target_date = allowed_dates[date_idx]
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Get session index on this day
        session_seq = day_sessions_count.get(date_str, 0)
        day_sessions_count[date_str] = session_seq + 1
        
        # Calculate time slot
        if target_date.strftime("%A").lower() in ["saturday", "sunday"]:
            s_min = pref_start_min + session_seq * pref_duration
            e_min = s_min + pref_duration
        else:
            s_min = start_min + session_seq * duration
            e_min = s_min + duration
            
        # Adjust for midnight rollover (if s_min is 1440 minutes or more)
        days_shift = s_min // 1440
        session_date = target_date + timedelta(days=days_shift)
        
        s_min_day = s_min % 1440
        e_min_day = e_min % 1440
        
        # If e_min_day ends up equal to s_min_day due to modulo, keep duration separate to avoid 0-duration ranges
        if e_min_day == s_min_day:
            e_min_day = s_min_day + (e_min - s_min)
            
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

