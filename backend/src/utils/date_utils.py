"""Date and time utilities for the mindframe application"""

from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, Union, List, Dict, Any
import calendar
from dateutil import parser, tz
from dateutil.relativedelta import relativedelta
import pytz


class DateUtils:
    """Utility class for date and time operations"""
    
    # Common date formats
    ISO_FORMAT = '%Y-%m-%d'
    ISO_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
    ISO_DATETIME_TZ_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    US_FORMAT = '%m/%d/%Y'
    EU_FORMAT = '%d/%m/%Y'
    DISPLAY_FORMAT = '%B %d, %Y'
    DISPLAY_DATETIME_FORMAT = '%B %d, %Y at %I:%M %p'
    
    @staticmethod
    def now(timezone_name: str = 'UTC') -> datetime:
        """Get current datetime in specified timezone
        
        Args:
            timezone_name: Timezone name (e.g., 'UTC', 'US/Eastern')
            
        Returns:
            datetime: Current datetime in specified timezone
        """
        tz_obj = pytz.timezone(timezone_name)
        return datetime.now(tz_obj)
    
    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime
        
        Returns:
            datetime: Current UTC datetime
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def today(timezone_name: str = 'UTC') -> date:
        """Get today's date in specified timezone
        
        Args:
            timezone_name: Timezone name
            
        Returns:
            date: Today's date
        """
        return DateUtils.now(timezone_name).date()
    
    @staticmethod
    def parse_date(date_string: str, date_format: str = None) -> Optional[datetime]:
        """Parse date string into datetime object
        
        Args:
            date_string: Date string to parse
            date_format: Optional format string
            
        Returns:
            Optional[datetime]: Parsed datetime or None if parsing fails
        """
        if not date_string:
            return None
        
        try:
            if date_format:
                return datetime.strptime(date_string, date_format)
            else:
                # Use dateutil parser for flexible parsing
                return parser.parse(date_string)
        except (ValueError, TypeError, parser.ParserError):
            return None
    
    @staticmethod
    def format_date(dt: Union[datetime, date], format_string: str = ISO_FORMAT) -> str:
        """Format date/datetime object to string
        
        Args:
            dt: Date or datetime object
            format_string: Format string
            
        Returns:
            str: Formatted date string
        """
        if not dt:
            return ''
        return dt.strftime(format_string)
    
    @staticmethod
    def format_datetime_for_display(dt: datetime, include_timezone: bool = True) -> str:
        """Format datetime for user-friendly display
        
        Args:
            dt: Datetime object
            include_timezone: Whether to include timezone info
            
        Returns:
            str: Formatted datetime string
        """
        if not dt:
            return ''
        
        formatted = dt.strftime(DateUtils.DISPLAY_DATETIME_FORMAT)
        
        if include_timezone and dt.tzinfo:
            tz_name = dt.tzinfo.tzname(dt)
            formatted += f" ({tz_name})"
        
        return formatted
    
    @staticmethod
    def convert_timezone(dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime from one timezone to another
        
        Args:
            dt: Datetime object
            from_tz: Source timezone name
            to_tz: Target timezone name
            
        Returns:
            datetime: Converted datetime
        """
        if dt.tzinfo is None:
            # Assume the datetime is in the from_tz
            from_timezone = pytz.timezone(from_tz)
            dt = from_timezone.localize(dt)
        
        to_timezone = pytz.timezone(to_tz)
        return dt.astimezone(to_timezone)
    
    @staticmethod
    def to_utc(dt: datetime, source_tz: str = None) -> datetime:
        """Convert datetime to UTC
        
        Args:
            dt: Datetime object
            source_tz: Source timezone (if dt is naive)
            
        Returns:
            datetime: UTC datetime
        """
        if dt.tzinfo is None and source_tz:
            source_timezone = pytz.timezone(source_tz)
            dt = source_timezone.localize(dt)
        
        return dt.astimezone(pytz.UTC)
    
    @staticmethod
    def from_utc(dt: datetime, target_tz: str) -> datetime:
        """Convert UTC datetime to target timezone
        
        Args:
            dt: UTC datetime object
            target_tz: Target timezone name
            
        Returns:
            datetime: Datetime in target timezone
        """
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        target_timezone = pytz.timezone(target_tz)
        return dt.astimezone(target_timezone)
    
    @staticmethod
    def add_time(dt: datetime, **kwargs) -> datetime:
        """Add time to datetime
        
        Args:
            dt: Datetime object
            **kwargs: Time components (days, hours, minutes, seconds, etc.)
            
        Returns:
            datetime: New datetime with added time
        """
        return dt + timedelta(**kwargs)
    
    @staticmethod
    def subtract_time(dt: datetime, **kwargs) -> datetime:
        """Subtract time from datetime
        
        Args:
            dt: Datetime object
            **kwargs: Time components (days, hours, minutes, seconds, etc.)
            
        Returns:
            datetime: New datetime with subtracted time
        """
        return dt - timedelta(**kwargs)
    
    @staticmethod
    def add_months(dt: datetime, months: int) -> datetime:
        """Add months to datetime
        
        Args:
            dt: Datetime object
            months: Number of months to add
            
        Returns:
            datetime: New datetime with added months
        """
        return dt + relativedelta(months=months)
    
    @staticmethod
    def add_years(dt: datetime, years: int) -> datetime:
        """Add years to datetime
        
        Args:
            dt: Datetime object
            years: Number of years to add
            
        Returns:
            datetime: New datetime with added years
        """
        return dt + relativedelta(years=years)
    
    @staticmethod
    def get_age(birth_date: Union[datetime, date], reference_date: Union[datetime, date] = None) -> int:
        """Calculate age from birth date
        
        Args:
            birth_date: Birth date
            reference_date: Reference date (defaults to today)
            
        Returns:
            int: Age in years
        """
        if reference_date is None:
            reference_date = date.today()
        
        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        if isinstance(reference_date, datetime):
            reference_date = reference_date.date()
        
        age = reference_date.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age
    
    @staticmethod
    def get_time_difference(dt1: datetime, dt2: datetime) -> Dict[str, int]:
        """Get time difference between two datetimes
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            Dict: Time difference components
        """
        diff = abs(dt2 - dt1)
        
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'total_seconds': int(diff.total_seconds())
        }
    
    @staticmethod
    def format_time_ago(dt: datetime, reference_dt: datetime = None) -> str:
        """Format datetime as 'time ago' string
        
        Args:
            dt: Datetime to format
            reference_dt: Reference datetime (defaults to now)
            
        Returns:
            str: Formatted 'time ago' string
        """
        if reference_dt is None:
            reference_dt = DateUtils.utc_now()
        
        diff = reference_dt - dt
        
        if diff.days > 0:
            if diff.days == 1:
                return "1 day ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif diff.days < 365:
                months = diff.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = diff.days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
        
        seconds = diff.seconds
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
    
    @staticmethod
    def get_start_of_day(dt: datetime) -> datetime:
        """Get start of day (00:00:00) for given datetime
        
        Args:
            dt: Datetime object
            
        Returns:
            datetime: Start of day
        """
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_day(dt: datetime) -> datetime:
        """Get end of day (23:59:59.999999) for given datetime
        
        Args:
            dt: Datetime object
            
        Returns:
            datetime: End of day
        """
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def get_start_of_week(dt: datetime, start_day: int = 0) -> datetime:
        """Get start of week for given datetime
        
        Args:
            dt: Datetime object
            start_day: Start day of week (0=Monday, 6=Sunday)
            
        Returns:
            datetime: Start of week
        """
        days_since_start = (dt.weekday() - start_day) % 7
        start_of_week = dt - timedelta(days=days_since_start)
        return DateUtils.get_start_of_day(start_of_week)
    
    @staticmethod
    def get_start_of_month(dt: datetime) -> datetime:
        """Get start of month for given datetime
        
        Args:
            dt: Datetime object
            
        Returns:
            datetime: Start of month
        """
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_month(dt: datetime) -> datetime:
        """Get end of month for given datetime
        
        Args:
            dt: Datetime object
            
        Returns:
            datetime: End of month
        """
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        return dt.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def get_business_days(start_date: date, end_date: date) -> int:
        """Get number of business days between two dates
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            int: Number of business days
        """
        business_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                business_days += 1
            current_date += timedelta(days=1)
        
        return business_days
    
    @staticmethod
    def is_weekend(dt: Union[datetime, date]) -> bool:
        """Check if date is weekend
        
        Args:
            dt: Date or datetime object
            
        Returns:
            bool: True if weekend, False otherwise
        """
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt.weekday() >= 5  # Saturday = 5, Sunday = 6
    
    @staticmethod
    def is_business_day(dt: Union[datetime, date]) -> bool:
        """Check if date is a business day
        
        Args:
            dt: Date or datetime object
            
        Returns:
            bool: True if business day, False otherwise
        """
        return not DateUtils.is_weekend(dt)
    
    @staticmethod
    def get_quarter(dt: Union[datetime, date]) -> int:
        """Get quarter for given date
        
        Args:
            dt: Date or datetime object
            
        Returns:
            int: Quarter (1-4)
        """
        if isinstance(dt, datetime):
            month = dt.month
        else:
            month = dt.month
        
        return (month - 1) // 3 + 1
    
    @staticmethod
    def get_week_number(dt: Union[datetime, date]) -> int:
        """Get ISO week number for given date
        
        Args:
            dt: Date or datetime object
            
        Returns:
            int: ISO week number
        """
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt.isocalendar()[1]
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime, max_days: int = None) -> bool:
        """Validate date range
        
        Args:
            start_date: Start date
            end_date: End date
            max_days: Maximum allowed days in range
            
        Returns:
            bool: True if valid, False otherwise
        """
        if start_date >= end_date:
            return False
        
        if max_days:
            diff = (end_date - start_date).days
            if diff > max_days:
                return False
        
        return True
    
    @staticmethod
    def get_available_timezones() -> List[str]:
        """Get list of available timezone names
        
        Returns:
            List[str]: List of timezone names
        """
        return list(pytz.all_timezones)
    
    @staticmethod
    def get_common_timezones() -> List[str]:
        """Get list of common timezone names
        
        Returns:
            List[str]: List of common timezone names
        """
        return list(pytz.common_timezones)