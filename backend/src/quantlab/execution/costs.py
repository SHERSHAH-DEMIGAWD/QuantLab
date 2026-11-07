"""Approved flat commission and adverse basis-point slippage, using Decimal."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

CENT = Decimal("0.01")
PRICE_UNIT = Decimal("0.000001")


def effective_price(open_price: Decimal, side: Literal["BUY", "SELL"], slippage_bps: Decimal) -> Decimal:
    """Called with validated inputs inside the engine's precision-28 context."""
    fraction = slippage_bps / Decimal("10000")
    factor = 1 + fraction if side == "BUY" else 1 - fraction
    return (open_price * factor).quantize(PRICE_UNIT, rounding=ROUND_HALF_UP)


def commission_per_fill(configured: Decimal) -> Decimal:
    return configured.quantize(CENT, rounding=ROUND_HALF_UP)
