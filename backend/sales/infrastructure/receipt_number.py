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
        highest = 0
        numbers = SaleModel.objects.filter(receipt_number__startswith=prefix).values_list(
            "receipt_number", flat=True
        )
        for number in numbers:
            try:
                highest = max(highest, int(number.split("-")[-1]))
            except (ValueError, IndexError):
                continue
        return f"{prefix}{highest + 1:06d}"
