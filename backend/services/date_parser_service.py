"""Service for parsing date and time references from text"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as dateutil_parse
import logging

logger = logging.getLogger(__name__)

class DateParserService:
    """Parse time references from email content"""
    
    def __init__(self):
        # Quarter definitions
        self.quarters = {
            1: (1, 1),   # Q1: Jan 1
            2: (4, 1),   # Q2: Apr 1
            3: (7, 1),   # Q3: Jul 1
            4: (10, 1),  # Q4: Oct 1
        }
        
        # Season definitions (Northern Hemisphere)
        self.seasons = {
            'spring': (3, 20),   # March 20
            'summer': (6, 21),   # June 21
            'fall': (9, 22),     # September 22
            'autumn': (9, 22),   # September 22 (alias)
            'winter': (12, 21),  # December 21
        }
    
    def get_current_datetime(self) -> datetime:
        """Get current datetime with timezone"""
        return datetime.now(timezone.utc)
    
    def parse_time_references(self, text: str) -> List[Tuple[str, datetime, str]]:
        """
        Parse all time references from text
        Returns list of (matched_text, target_datetime, context)
        """
        results = []
        current_date = self.get_current_datetime()
        
        # Pattern 1: "next quarter" / "3rd quarter" / "Q3"
        quarter_patterns = [
            r'(?:check|contact|follow up|follow-up|touch base|get back|reach out|reconnect|circle back).*?(?:in|next|during|for)\s+(?:the\s+)?(?:next\s+)?(?:(\d+)(?:st|nd|rd|th)?\s+)?quarter',
            r'(?:check|contact|follow up|follow-up|touch base|get back|reach out|reconnect|circle back).*?(?:Q(\d))',
            r'(?:in|next|during)\s+(?:the\s+)?(?:next\s+)?(?:(\d+)(?:st|nd|rd|th)?\s+)?quarter',
            r'(?:Q(\d))\b',
        ]
        
        for pattern in quarter_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                quarter_num = None
                if match.group(1):
                    quarter_num = int(match.group(1))
                
                target_date = self._parse_quarter_reference(current_date, quarter_num)
                if target_date:
                    context = self._extract_context(text, match.start(), match.end())
                    results.append((match.group(0), target_date, context))
        
        # Pattern 2: "next week" / "next month" / "next year"
        relative_patterns = [
            (r'next\s+week', lambda d: d + timedelta(weeks=1)),
            (r'next\s+month', lambda d: d + relativedelta(months=1)),
            (r'next\s+year', lambda d: d + relativedelta(years=1)),
            (r'in\s+(\d+)\s+months?', lambda d, m: d + relativedelta(months=int(m))),
        ]
        
        for pattern, calculator in relative_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match.groups()) > 0:
                        target_date = calculator(current_date, *[g for g in match.groups() if g])
                    else:
                        target_date = calculator(current_date)
                    
                    context = self._extract_context(text, match.start(), match.end())
                    results.append((match.group(0), target_date, context))
                except Exception as e:
                    logger.error(f"Error calculating relative date: {e}")
        
        # Pattern 2.5: Week ranges "in 2-3 weeks" / "after 2-3 weeks"
        week_range_matches = re.finditer(r'(?:in|after)\s+(\d+)\s*[-–]\s*(\d+)\s+weeks?', text, re.IGNORECASE)
        for match in week_range_matches:
            try:
                w1 = int(match.group(1))
                w2 = int(match.group(2))
                avg_weeks = (w1 + w2) // 2
                target_date = current_date + timedelta(weeks=avg_weeks)
                context = self._extract_context(text, match.start(), match.end())
                results.append((match.group(0), target_date, context))
            except Exception as e:
                logger.error(f"Error calculating week range: {e}")
        
        # Pattern 2.6: Simple week reference "in X weeks" / "after X weeks"
        week_simple_matches = re.finditer(r'(?:in|after)\s+(\d+)\s+weeks?', text, re.IGNORECASE)
        for match in week_simple_matches:
            try:
                weeks = int(match.group(1))
                target_date = current_date + timedelta(weeks=weeks)
                context = self._extract_context(text, match.start(), match.end())
                results.append((match.group(0), target_date, context))
            except Exception as e:
                logger.error(f"Error calculating week reference: {e}")
        
        # Pattern 3: Day-based references
        # "after X days" / "in X days"
        day_simple_matches = re.finditer(r'(?:after|in)\s+(\d+)\s+days?', text, re.IGNORECASE)
        for match in day_simple_matches:
            try:
                days = int(match.group(1))
                target_date = current_date + timedelta(days=days)
                context = self._extract_context(text, match.start(), match.end())
                results.append((match.group(0), target_date, context))
            except Exception as e:
                logger.error(f"Error calculating day reference: {e}")
        
        # "after 10-15 days" / "in 10-15 days"
        day_range_matches = re.finditer(r'(?:after|in)\s+(\d+)\s*[-–]\s*(\d+)\s+days?', text, re.IGNORECASE)
        for match in day_range_matches:
            try:
                d1 = int(match.group(1))
                d2 = int(match.group(2))
                avg_days = (d1 + d2) // 2
                target_date = current_date + timedelta(days=avg_days)
                context = self._extract_context(text, match.start(), match.end())
                results.append((match.group(0), target_date, context))
            except Exception as e:
                logger.error(f"Error calculating day range: {e}")
        
        # "couple of days" / "few days"
        vague_day_matches = re.finditer(r'(?:in\s+)?(?:a\s+)?(?:couple|few)\s+(?:of\s+)?days', text, re.IGNORECASE)
        for match in vague_day_matches:
            try:
                target_date = current_date + timedelta(days=3)
                context = self._extract_context(text, match.start(), match.end())
                results.append((match.group(0), target_date, context))
            except Exception as e:
                logger.error(f"Error calculating vague day reference: {e}")
        
        # Pattern 4: Season-based references
        # "next summer" / "next winter" / "next spring" / "next fall" / "this summer"
        season_patterns = [
            r'(?:next|this\s+coming|upcoming)\s+(spring|summer|fall|autumn|winter)',
            r'(?:check|contact|follow up|follow-up|touch base|get back|reach out|reconnect|circle back).*?(?:in|next|during|this)\s+(?:the\s+)?(?:coming\s+)?(spring|summer|fall|autumn|winter)',
        ]
        
        for pattern in season_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    season_name = match.group(1).lower()
                    target_date = self._parse_season_reference(current_date, season_name)
                    if target_date:
                        context = self._extract_context(text, match.start(), match.end())
                        results.append((match.group(0), target_date, context))
                except Exception as e:
                    logger.error(f"Error calculating season date: {e}")
        
        # Pattern 5: Specific dates like "20th November", "November 20", "21st Dec"
        # Exclude time units (days, weeks, months, years) from matching as month names
        time_units = {'days', 'day', 'weeks', 'week', 'months', 'month', 'years', 'year', 
                      'hours', 'hour', 'minutes', 'minute', 'spring', 'summer', 'fall', 'autumn', 'winter'}
        
        date_patterns = [
            r'(?:till|until|after|on|by)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+)',
            r'(?:till|until|after|on|by)\s+([A-Za-z]+)\s+(\d+)(?:st|nd|rd|th)?',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = [g for g in match.groups() if g]
                    # Skip if any group is a time unit word
                    if any(g.lower() in time_units for g in groups):
                        continue
                    date_str = ' '.join(groups)
                    target_date = self._parse_specific_date(date_str, current_date)
                    if target_date:
                        context = self._extract_context(text, match.start(), match.end())
                        results.append((match.group(0), target_date, context))
                except Exception as e:
                    logger.error(f"Error parsing specific date: {e}")
        
        # Pattern 6: "next year same time" / "next year 2nd month"
        special_patterns = [
            (r'next\s+year\s+same\s+time', lambda d: d + relativedelta(years=1)),
            (r'next\s+year\s+(\d+)(?:st|nd|rd|th)?\s+month', 
             lambda d, m: datetime(d.year + 1, int(m), 1, tzinfo=timezone.utc)),
        ]
        
        for pattern, calculator in special_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match.groups()) > 0:
                        target_date = calculator(current_date, *[g for g in match.groups() if g])
                    else:
                        target_date = calculator(current_date)
                    
                    context = self._extract_context(text, match.start(), match.end())
                    results.append((match.group(0), target_date, context))
                except Exception as e:
                    logger.error(f"Error calculating special date: {e}")
        
        # Pattern 7: "beginning of next year" / "start of next year" / "end of year"
        year_boundary_patterns = [
            (r'(?:beginning|start)\s+of\s+(?:next|the\s+next)\s+year', 
             lambda d: datetime(d.year + 1, 1, 2, 9, 0, 0, tzinfo=timezone.utc)),
            (r'(?:end|close)\s+of\s+(?:this\s+|the\s+)?year',
             lambda d: datetime(d.year, 12, 15, 9, 0, 0, tzinfo=timezone.utc)),
            (r'(?:beginning|start)\s+of\s+(?:next|the\s+next)\s+month',
             lambda d: (d + relativedelta(months=1)).replace(day=1, hour=9, minute=0, second=0)),
            (r'(?:end|close)\s+of\s+(?:this\s+|the\s+)?month',
             lambda d: (d + relativedelta(months=1)).replace(day=1, hour=9, minute=0, second=0) - timedelta(days=5)),
            (r'(?:next\s+)?(?:fiscal|financial)\s+year',
             lambda d: datetime(d.year + 1, 4, 1, 9, 0, 0, tzinfo=timezone.utc)),
        ]
        
        for pattern, calculator in year_boundary_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    target_date = calculator(current_date)
                    context = self._extract_context(text, match.start(), match.end())
                    results.append((match.group(0), target_date, context))
                except Exception as e:
                    logger.error(f"Error calculating year boundary date: {e}")
        
        # Pattern 8: "out of office till" / "will be free after"
        availability_patterns = [
            r'out\s+of\s+office\s+(?:till|until)\s+(.+?)(?:\.|,|$)',
            r'will\s+be\s+(?:free|available)\s+(?:after|from)\s+(.+?)(?:\.|,|$)',
            r'(?:back|available|free)\s+(?:on|after|from)\s+(.+?)(?:\.|,|$)',
        ]
        
        for pattern in availability_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_text = match.group(1).strip()
                    target_date = self._parse_flexible_date(date_text, current_date)
                    if target_date:
                        context = self._extract_context(text, match.start(), match.end())
                        results.append((match.group(0), target_date, context))
                except Exception as e:
                    logger.error(f"Error parsing availability date: {e}")
        
        # Pattern 9: Named day references
        # "next Monday" / "next Friday" etc.
        day_names = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        day_name_matches = re.finditer(
            r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            text, re.IGNORECASE
        )
        for match in day_name_matches:
            try:
                target_day = day_names[match.group(1).lower()]
                days_ahead = target_day - current_date.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = current_date + timedelta(days=days_ahead)
                target_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                context = self._extract_context(text, match.start(), match.end())
                results.append((match.group(0), target_date, context))
            except Exception as e:
                logger.error(f"Error calculating named day reference: {e}")
        
        # Remove duplicates and sort by target date
        unique_results = []
        seen_dates = set()
        for matched_text, target_date, context in results:
            date_key = target_date.date()
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                unique_results.append((matched_text, target_date, context))
        
        unique_results.sort(key=lambda x: x[1])
        return unique_results
    
    def _parse_season_reference(self, current_date: datetime, season_name: str) -> Optional[datetime]:
        """Parse season reference and return target date (start of season)"""
        season_name = season_name.lower()
        if season_name not in self.seasons:
            return None
        
        month, day = self.seasons[season_name]
        
        # Try current year first
        target = datetime(current_date.year, month, day, 9, 0, 0, tzinfo=timezone.utc)
        
        # If the season start has passed, use next year
        if target <= current_date:
            target = datetime(current_date.year + 1, month, day, 9, 0, 0, tzinfo=timezone.utc)
        
        return target
    
    def _parse_quarter_reference(self, current_date: datetime, quarter_num: Optional[int] = None) -> Optional[datetime]:
        """Parse quarter reference and return target date"""
        current_quarter = (current_date.month - 1) // 3 + 1
        
        if quarter_num is None:
            # "next quarter"
            target_quarter = current_quarter + 1 if current_quarter < 4 else 1
            target_year = current_date.year if current_quarter < 4 else current_date.year + 1
        else:
            # Specific quarter number
            if quarter_num < 1 or quarter_num > 4:
                return None
            
            if quarter_num > current_quarter:
                # Same year
                target_quarter = quarter_num
                target_year = current_date.year
            else:
                # Next year
                target_quarter = quarter_num
                target_year = current_date.year + 1
        
        # Get month and day for quarter
        month, day = self.quarters[target_quarter]
        return datetime(target_year, month, day, 9, 0, 0, tzinfo=timezone.utc)
    
    def _parse_specific_date(self, date_str: str, current_date: datetime) -> Optional[datetime]:
        """Parse specific date like '20th November' or 'November 20'"""
        try:
            # Use dateutil parser
            parsed_date = dateutil_parse(date_str, fuzzy=True)
            
            # If year is not in string, assume current year or next year
            if parsed_date.year == current_date.year or parsed_date.year == 1900:
                # Determine if date is in past
                test_date = datetime(current_date.year, parsed_date.month, parsed_date.day, tzinfo=timezone.utc)
                if test_date < current_date:
                    # Use next year
                    parsed_date = datetime(current_date.year + 1, parsed_date.month, parsed_date.day, 9, 0, 0, tzinfo=timezone.utc)
                else:
                    # Use current year
                    parsed_date = datetime(current_date.year, parsed_date.month, parsed_date.day, 9, 0, 0, tzinfo=timezone.utc)
            else:
                # Year was specified, use it
                parsed_date = datetime(parsed_date.year, parsed_date.month, parsed_date.day, 9, 0, 0, tzinfo=timezone.utc)
            
            return parsed_date
        except Exception as e:
            logger.error(f"Error parsing specific date '{date_str}': {e}")
            return None
    
    def _parse_flexible_date(self, date_text: str, current_date: datetime) -> Optional[datetime]:
        """Parse flexible date formats"""
        date_text_lower = date_text.lower().strip()
        
        # Relative references
        if 'next week' in date_text_lower:
            return current_date + timedelta(weeks=1)
        elif 'next month' in date_text_lower:
            return current_date + relativedelta(months=1)
        elif 'next year' in date_text_lower:
            return current_date + relativedelta(years=1)
        
        # Season references
        for season_name in self.seasons:
            if season_name in date_text_lower:
                return self._parse_season_reference(current_date, season_name)
        
        # Day ranges "10-15 days"
        day_range_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s+days?', date_text_lower)
        if day_range_match:
            d1 = int(day_range_match.group(1))
            d2 = int(day_range_match.group(2))
            avg_days = (d1 + d2) // 2
            return current_date + timedelta(days=avg_days)
        
        # Simple day reference "X days"
        day_match = re.search(r'(\d+)\s+days?', date_text_lower)
        if day_match:
            days = int(day_match.group(1))
            return current_date + timedelta(days=days)
        
        # Week ranges "2-3 weeks"
        week_range_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s+weeks?', date_text_lower)
        if week_range_match:
            w1 = int(week_range_match.group(1))
            w2 = int(week_range_match.group(2))
            avg_weeks = (w1 + w2) // 2
            return current_date + timedelta(weeks=avg_weeks)
        
        # Simple week reference "X weeks"
        week_match = re.search(r'(\d+)\s+weeks?', date_text_lower)
        if week_match:
            weeks = int(week_match.group(1))
            return current_date + timedelta(weeks=weeks)
        
        # Try to parse as specific date
        return self._parse_specific_date(date_text, current_date)
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around matched text"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        context = text[context_start:context_end].strip()
        return context
    
    def should_create_followup(self, text: str) -> bool:
        """Check if email content contains time-based follow-up request"""
        time_refs = self.parse_time_references(text)
        return len(time_refs) > 0
    
    def get_followup_dates(self, base_date: datetime, intervals: List[int] = [2, 4, 6]) -> List[datetime]:
        """
        Calculate follow-up dates based on base date
        Default: 2, 4, 6 days after base date
        """
        return [base_date + timedelta(days=interval) for interval in intervals]
