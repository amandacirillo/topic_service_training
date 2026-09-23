"""Low-inventory alerting: notify when a non-reusable list's active topic
count drops below an absolute or percentage threshold.

The notification channel is abstracted behind NotificationSender so tests
never need real AWS credentials or network access -- only SesNotificationSender
touches boto3.
"""
from typing import Protocol

from app.settings import settings


class NotificationSender(Protocol):
    def send(self, subject: str, body: str) -> None: ...


class NullNotificationSender:
    """Used in tests/local dev: records what would have been sent instead of sending it."""

    def __init__(self):
        self.sent = []

    def send(self, subject: str, body: str) -> None:
        self.sent.append((subject, body))


class SesNotificationSender:
    def send(self, subject: str, body: str) -> None:
        import boto3

        client = boto3.client('ses', region_name=settings.aws_region)
        client.send_email(
            Source=settings.alert_email_from,
            Destination={'ToAddresses': [settings.alert_email_to]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}},
            },
        )


def is_low_inventory(active_count: int, total_count: int) -> bool:
    if total_count == 0:
        return False
    below_absolute = active_count <= settings.low_inventory_absolute
    below_percent = (active_count / total_count) < settings.low_inventory_percent
    return below_absolute or below_percent


def maybe_alert(topic_list, sender: NotificationSender) -> bool:
    """Send a low-inventory alert for a non-reusable list if it has crossed
    the threshold. Returns True if an alert was sent."""
    if topic_list.reusable:
        return False

    active = topic_list.active_count()
    total = topic_list.total_count()
    if not is_low_inventory(active, total):
        return False

    sender.send(
        subject=f'Low inventory: "{topic_list.name}"',
        body=(
            f'Topic list "{topic_list.name}" has {active} active topic(s) '
            f'out of {total} total. Consider adding more topics soon.'
        ),
    )
    return True
