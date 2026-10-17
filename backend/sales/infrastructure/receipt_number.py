from datetime import datetime

from sales.application.ports import ReceiptNumberPort


class SequentialReceiptNumberPort(ReceiptNumberPort):
    def generate(self) -> str:
        now = datetime.now()
        return f"ST-{now.year}-{now.month:02d}{now.day:02d}-{now.hour:02d}{now.minute:02d}{now.second:02d}"


class DatabaseReceiptNumberPort(ReceiptNumberPort):
    def generate(self) -> str:
        from sales.infrastructure.models import SaleModel

        now = datetime.now()
        prefix = f"ST-{now.year}-"
        last = SaleModel.objects.filter(receipt_number__startswith=prefix).order_by("-id").first()
        if last:
            try:
                seq = int(last.receipt_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"
