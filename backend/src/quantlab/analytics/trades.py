"""Full-entry/full-exit trade accounting, without treating open positions as trades."""

from collections.abc import Sequence
from decimal import Decimal, localcontext

from quantlab.execution import Fill
from quantlab.execution.engine import ARITHMETIC

from .models import AnalyticsError, ClosedTrade, Metric, OpenPosition, TradeStatistics


def analyze_trades(fills: Sequence[Fill], last_close: Decimal) -> TradeStatistics:
    """Consume engine fills; net P&L includes rounded commissions on both sides."""
    if not isinstance(last_close, Decimal) or not last_close.is_finite() or last_close <= 0:
        raise AnalyticsError("last_close must be a positive finite Decimal.")
    with localcontext(ARITHMETIC):
        entry = None
        closed = []
        previous_session = None
        for fill in fills:
            if not isinstance(fill, Fill) or type(fill.quantity) is not int or fill.quantity <= 0:
                raise AnalyticsError("Expected positive integer-quantity fills.")
            if previous_session is not None and fill.session <= previous_session:
                raise AnalyticsError("Expected fills in strictly ascending session order.")
            previous_session = fill.session
            if any(not isinstance(value, Decimal) or not value.is_finite() for value in (fill.notional, fill.fee, fill.cash_change)):
                raise AnalyticsError("Fill money must be finite Decimal.")
            if fill.notional < 0 or fill.fee < 0:
                raise AnalyticsError("Fill notional and fee must be nonnegative.")
            if fill.side == "BUY":
                if entry is not None or fill.cash_change != -(fill.notional + fill.fee):
                    raise AnalyticsError("Invalid full-entry fill accounting.")
                entry = fill
            elif fill.side == "SELL":
                if (entry is None or fill.quantity != entry.quantity
                        or fill.cash_change != fill.notional - fill.fee or fill.cash_change < 0):
                    raise AnalyticsError("Invalid full-exit fill accounting.")
                debit = -entry.cash_change
                closed.append(ClosedTrade(
                    entry_order_id=entry.order_id, exit_order_id=fill.order_id,
                    entry_session=entry.session, exit_session=fill.session,
                    quantity=entry.quantity, entry_debit=debit,
                    exit_credit=fill.cash_change, net_pnl=fill.cash_change - debit,
                ))
                entry = None
            else:
                raise AnalyticsError("Unknown fill side.")
        winners = sum(trade.net_pnl > 0 for trade in closed)
        losers = sum(trade.net_pnl < 0 for trade in closed)
        count = len(closed)
        open_position = None
        if entry is not None:
            marked = entry.quantity * last_close
            open_position = OpenPosition(
                entry_order_id=entry.order_id, entry_session=entry.session,
                quantity=entry.quantity, entry_debit=-entry.cash_change,
                last_close=last_close, market_value=marked, unrealized_pnl=marked + entry.cash_change,
            )
        return TradeStatistics(
            closed_trades=tuple(closed), closed_trade_count=count,
            winning_trades=winners, losing_trades=losers, break_even_trades=count - winners - losers,
            win_rate=Metric(winners / count) if count else Metric(None, "no_closed_trades"),
            mean_net_pnl=Metric(sum((trade.net_pnl for trade in closed), Decimal("0.00")) / count)
            if count else Metric(None, "no_closed_trades"),
            open_position=open_position,
        )
