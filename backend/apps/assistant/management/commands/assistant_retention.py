from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.assistant.models import GuestMerge, UsageLedger, UsageReservation


class Command(BaseCommand):
    help = "Delete expired content-free assistant ledger rows after their 12-month retention."

    def handle(self, *args, **options):
        today = timezone.now().date()
        with transaction.atomic():
            reservation_ids = list(
                UsageLedger.objects.select_for_update()
                .filter(retention_until__lt=today)
                .values_list("reservation_id", flat=True)
            )
            ledger_count, _ = UsageLedger.objects.filter(
                reservation_id__in=reservation_ids
            ).delete()
            reservation_count, _ = UsageReservation.objects.filter(pk__in=reservation_ids).delete()
            merge_count, _ = GuestMerge.objects.filter(
                created_at__lt=timezone.now() - timedelta(days=365)
            ).delete()
        self.stdout.write(
            f"assistant retention: ledger={ledger_count} reservations={reservation_count} "
            f"merges={merge_count}"
        )
