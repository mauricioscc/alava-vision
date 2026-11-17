"""ScheduleEngine - evaluates display rules for widgets and alerts."""

from datetime import datetime, date, time
from typing import Any
from core.models.schedule import ScheduleRule, RuleType, DayOfWeek


class ScheduleEngine:
    """Central service for evaluating scheduling rules.
    
    Determines if a widget or alert should be displayed based on
    time ranges, days of week, date ranges, and other rules.
    """

    @staticmethod
    def evaluate_rules(rules: list[ScheduleRule], current_time: datetime | None = None) -> bool:
        """Evaluate if all active rules are satisfied at the given time.
        
        Args:
            rules: List of ScheduleRule to evaluate.
            current_time: Time to evaluate against (defaults to now).
            
        Returns:
            True if ALL active rules are satisfied, or if there are no rules.
            False if ANY active rule is not satisfied.
        """
        if not rules:
            return True  # No rules means always allowed

        if current_time is None:
            current_time = datetime.now()

        active_rules = [r for r in rules if r.active]
        if not active_rules:
            return True

        return all(
            ScheduleEngine._evaluate_single_rule(rule, current_time)
            for rule in active_rules
        )

    @staticmethod
    def _evaluate_single_rule(rule: ScheduleRule, current_time: datetime) -> bool:
        """Evaluate a single rule against the current time."""
        match rule.rule_type:
            case RuleType.TIME_RANGE:
                return ScheduleEngine._evaluate_time_range(rule, current_time)
            case RuleType.DAY_OF_WEEK:
                return ScheduleEngine._evaluate_day_of_week(rule, current_time)
            case RuleType.DATE_RANGE:
                return ScheduleEngine._evaluate_date_range(rule, current_time)
            case RuleType.SPECIFIC_DATE:
                return ScheduleEngine._evaluate_specific_date(rule, current_time)
            case RuleType.SPECIFIC_DAY:
                return ScheduleEngine._evaluate_specific_day(rule, current_time)
            case _:
                return True

    @staticmethod
    def _evaluate_time_range(rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if current time is within the rule's time range."""
        if not rule.start_time or not rule.end_time:
            return True
        try:
            start = time.fromisoformat(rule.start_time)
            end = time.fromisoformat(rule.end_time)
            current = current_time.time()
            if start <= end:
                return start <= current <= end
            else:  #跨越 midnight
                return current >= start or current <= end
        except (ValueError, TypeError):
            return True

    @staticmethod
    def _evaluate_day_of_week(rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if current day is in the rule's allowed days."""
        if not rule.days_of_week:
            return True
        allowed_days = [d.strip().lower() for d in rule.days_of_week.split(",")]
        current_day = current_time.strftime("%A").lower()
        return current_day in allowed_days

    @staticmethod
    def _evaluate_date_range(rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if current date is within the rule's date range."""
        if not rule.start_date or not rule.end_date:
            return True
        try:
            start = date.fromisoformat(rule.start_date)
            end = date.fromisoformat(rule.end_date)
            current = current_time.date()
            return start <= current <= end
        except (ValueError, TypeError):
            return True

    @staticmethod
    def _evaluate_specific_date(rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if current date matches the rule's specific date."""
        if not rule.start_date:
            return True
        try:
            specific = date.fromisoformat(rule.start_date)
            return current_time.date() == specific
        except (ValueError, TypeError):
            return True

    @staticmethod
    def _evaluate_specific_day(rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if current day name matches the rule's specific day."""
        if not rule.days_of_week:
            return True
        allowed_days = [d.strip().lower() for d in rule.days_of_week.split(",")]
        current_day = current_time.strftime("%A").lower()
        return current_day in allowed_days

    @staticmethod
    def should_interrupt(current_priority: int, alert_priority: int) -> bool:
        """Determine if an alert should interrupt current content.
        
        Args:
            current_priority: Priority of the currently displayed content.
            alert_priority: Priority of the incoming alert.
            
        Returns:
            True if the alert should interrupt, False otherwise.
        """
        return alert_priority > current_priority