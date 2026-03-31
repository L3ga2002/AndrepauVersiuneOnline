def parse_number(s: str) -> float:
    """Parse a number string that might use comma as decimal separator"""
    s = s.strip()
    if '.' in s and ',' in s:
        if s.rindex('.') > s.rindex(','):
            s = s.replace(',', '')
        else:
            s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0
