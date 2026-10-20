import pytest

from inventory.domain.entities import MovementType


@pytest.mark.parametrize(
    "movement_type",
    [MovementType.SALE, MovementType.ADJUSTMENT_OUT, MovementType.WRITE_OFF],
)
def test_outgoing_movements_reduce_stock(movement_type):
    assert movement_type.reduces_stock is True


@pytest.mark.parametrize(
    "movement_type",
    [
        MovementType.OPENING,
        MovementType.PURCHASE,
        MovementType.REFUND_RETURN,
        MovementType.ADJUSTMENT_IN,
    ],
)
def test_incoming_movements_do_not_reduce_stock(movement_type):
    assert movement_type.reduces_stock is False
