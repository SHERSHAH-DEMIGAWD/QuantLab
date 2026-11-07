"""Sequential next-observed-open execution; no delivery dependencies."""

from dataclasses import replace
from datetime import date
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext

from quantlab.data import Bar, Dataset, ImportReport, Metadata
from quantlab.data.loader import validate_ohlc
from quantlab.strategies import BuyAndHold, StrategyConfig, StrategyError, create_rule

from .costs import CENT, commission_per_fill, effective_price
from .models import (
    DailyValuation, Decision, ExecutionSettings, Fill, Order,
    SimulationError, SimulationResult,
)

ENGINE_VERSION = "1.3.0"
MAX_CAPITAL = Decimal("999999999.99")
MAX_PRICE = Decimal("999999.999999")
# Repeated entries must remain within the precision-28 arithmetic envelope.
MAX_SHARES = 999999999999999
MAX_CASH = Decimal("999999999999999999999.99")
ARITHMETIC = Context(prec=28, rounding=ROUND_HALF_UP)
ASSUMPTIONS = (
    "Price-return simulation excluding dividends; not total shareholder return.",
    "One instrument, USD, daily bars, integer shares, long-only, no leverage or external cash flows.",
    "Decisions occur after the close; budgeted buys/full-position sells execute at the next observed open.",
    "Buy quantity is floor((reserved cash - rounded commission) / effective open); rounded-debit affordability is rechecked.",
    "Flat commission and adverse slippage follow recorded settings; only fills incur fees; no partial fills or automatic retries.",
    "Costs are simplified research assumptions, not a brokerage fee or opening-liquidity guarantee.",
    "Buy-and-hold may produce a fresh LONG intent at a rejected buy session's close; invested buy-and-hold holds.",
    "Zero-volume execution rejects the order; positive daily volume does not establish opening liquidity.",
    "Decimal precision 28; fill prices use six decimals, cash/notionals cents, ROUND_HALF_UP; marks are unrounded.",
    "Sale proceeds are immediately available; brokerage settlement restrictions are not modeled.",
    "Final holdings remain open; final-session pending orders expire without a fill or fee.",
    "No splits, dividends, reinvestment, interest, taxes, symbol changes, or delisting proceeds are modeled.",
    "Metadata declarations are assertions, not independently verified market facts or completeness evidence.",
)


def _decimal(value: Decimal, field: str, places: int, maximum: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise SimulationError(f"{field}: expected a finite Decimal, not float/int/string.")
    if value < 0 or value > maximum or value != value.quantize(Decimal(1).scaleb(-places)):
        raise SimulationError(f"{field}: supported range is 0..{maximum} with at most {places} fractional places.")


def _preflight(dataset: Dataset, capital: Decimal, settings: ExecutionSettings) -> tuple[tuple[Bar, ...], tuple[Bar, ...]]:
    _decimal(capital, "initial_capital", 2, MAX_CAPITAL)
    if capital <= 0:
        raise SimulationError("initial_capital must be positive.")
    _decimal(settings.commission_per_fill_usd, "commission_per_fill_usd", 6, MAX_CASH)
    _decimal(settings.slippage_bps, "slippage_bps", 6, Decimal("9999.999999"))
    if type(settings.acknowledge_unverified_coverage) is not bool:
        raise SimulationError("acknowledge_unverified_coverage must be bool.")
    for name in ("start_date", "end_date", "sell_after_session", "warmup_start_date", "warmup_end_date"):
        if getattr(settings, name) is not None and type(getattr(settings, name)) is not date:
            raise SimulationError(f"{name}: expected a date or None.")
    if settings.start_date and settings.end_date and settings.start_date > settings.end_date:
        raise SimulationError("start_date must not exceed end_date.")
    has_warmup = settings.warmup_start_date is not None or settings.warmup_end_date is not None
    if has_warmup and (
        settings.warmup_start_date is None or settings.warmup_end_date is None
        or settings.start_date is None
        or not settings.warmup_start_date <= settings.warmup_end_date < settings.start_date
    ):
        raise SimulationError("Warm-up requires both bounds, ordered strictly before an explicit evaluation start_date.")
    if (not isinstance(dataset, Dataset) or not isinstance(dataset.bars, tuple)
            or not dataset.bars or not isinstance(dataset.metadata, Metadata)
            or not isinstance(dataset.report, ImportReport)):
        raise SimulationError("Expected a nonempty validated Phase 1 Dataset.")
    metadata = dataset.metadata
    if (metadata.contract_version != 1 or metadata.currency != "USD"
            or metadata.frequency != "1d" or metadata.session_timezone != "America/New_York"
            or metadata.source_kind not in ("synthetic", "local_file")):
        raise SimulationError("Unsupported dataset contract, currency, frequency, timezone, or source kind.")
    if (metadata.adjustment_basis != "unadjusted" or metadata.ohlc_basis_consistent is not True
            or metadata.volume_basis != "raw" or metadata.split_status != "none_reported"
            or not isinstance(metadata.split_evidence, str)
            or not metadata.split_evidence.strip() or metadata.split_evidence.strip().lower() == "unknown"):
        raise SimulationError("D04 eligibility requires consistent unadjusted OHLC, raw volume, none_reported splits and explicit split evidence.")
    if metadata.source_kind == "local_file" and not settings.acknowledge_unverified_coverage:
        raise SimulationError("Real-data session coverage is unverified; explicit acknowledgment is required even if declared_complete.")
    report = dataset.report
    # Check structure across the imported input; arithmetic limits apply to the selected window.
    previous = None
    selected = []
    warmup = []
    for bar in dataset.bars:
        if not isinstance(bar, Bar) or type(bar.date) is not date or (previous and bar.date <= previous):
            raise SimulationError("Bars must have strictly ascending unique session dates.")
        previous = bar.date
        if type(bar.volume) is not int or bar.volume < 0:
            raise SimulationError(f"{bar.date}: volume must be a nonnegative integer.")
        in_warmup = has_warmup and settings.warmup_start_date <= bar.date <= settings.warmup_end_date
        in_evaluation = ((settings.start_date is None or bar.date >= settings.start_date)
                         and (settings.end_date is None or bar.date <= settings.end_date))
        if not in_warmup and not in_evaluation:
            continue
        for field in ("open", "high", "low", "close"):
            value = getattr(bar, field)
            _decimal(value, f"{bar.date}.{field}", 6, MAX_PRICE)
            if value <= 0:
                raise SimulationError(f"{bar.date}.{field}: price must be positive.")
        if not validate_ohlc(bar.open, bar.high, bar.low, bar.close):
            raise SimulationError(f"{bar.date}: invalid OHLC relationships.")
        if in_warmup:
            warmup.append(bar)
        else:
            selected.append(bar)
    if (report.row_count != len(dataset.bars) or report.first_date != dataset.bars[0].date
            or report.last_date != dataset.bars[-1].date or report.coverage_assessment != "unverified"):
        raise SimulationError("Dataset/report mismatch; use the validated Phase 1 importer.")
    if len(selected) < 2:
        raise SimulationError("At least two observed sessions are required in the evaluation window.")
    if settings.sell_after_session and not any(bar.date == settings.sell_after_session for bar in selected):
        raise SimulationError("sell_after_session must name an observed evaluation session.")
    if has_warmup and not warmup:
        raise SimulationError("The warm-up interval must contain an observed session.")
    return tuple(selected), tuple(warmup)


def validate_simulation_request(
    dataset: Dataset, initial_capital: Decimal, strategy: StrategyConfig,
    settings: ExecutionSettings,
) -> tuple[int, int]:
    """Preflight without trading; return evaluated and warm-up bar counts."""
    if not isinstance(settings, ExecutionSettings):
        raise SimulationError("settings must be ExecutionSettings.")
    try:
        create_rule(strategy, sell_after_session=settings.sell_after_session)
    except StrategyError as exc:
        raise SimulationError(str(exc)) from exc
    with localcontext(ARITHMETIC):
        bars, warmup = _preflight(dataset, initial_capital, settings)
    return len(bars), len(warmup)


def _execute(
    order: Order, bar: Bar, cash: Decimal, shares: int,
    settings: ExecutionSettings = ExecutionSettings(),
) -> tuple[Order, Fill | None]:
    price = effective_price(bar.open, order.side, settings.slippage_bps)
    fee = commission_per_fill(settings.commission_per_fill_usd)
    outcome = replace(order, outcome_session=bar.date, base_open=bar.open, effective_price=price)
    reason = None
    quantity = 0
    notional = Decimal("0.00")
    if order.eligible_session != bar.date or bar.date <= order.decision_session:
        raise SimulationError("Order timing invariant failed.")
    if bar.volume == 0:
        reason = "zero_volume"
    elif price <= 0:
        reason = "nonpositive_effective_price"
    elif order.side == "BUY":
        if shares != 0 or order.budget is None or order.budget > cash:
            reason = "invalid_buy_state"
        else:
            # Integer microunits give exact floor sizing, independent of division rounding.
            available = max(order.budget - fee, Decimal("0.00"))
            quantity = int(available.scaleb(6)) // int(price.scaleb(6))
            if quantity > MAX_SHARES:
                raise SimulationError("Share quantity exceeds the supported precision-28 range.")
            notional = (quantity * price).quantize(CENT)
            while quantity > 0 and (notional + fee > cash or notional + fee > order.budget):
                quantity -= 1
                notional = (quantity * price).quantize(CENT)
            if quantity == 0:
                reason = "insufficient_capital"
    elif order.requested_shares != shares or shares <= 0:
        reason = "invalid_sell_position"
    else:
        quantity = shares
        notional = (quantity * price).quantize(CENT)
        if notional < fee:
            reason = "proceeds_below_fee"
    if reason:
        return replace(outcome, status="REJECTED", reason=reason), None
    change = -(notional + fee) if order.side == "BUY" else notional - fee
    fill = Fill(
        order_id=order.order_id, session=bar.date, side=order.side, quantity=quantity,
        base_open=bar.open, effective_price=price, notional=notional,
        fee=fee, cash_change=change,
    )
    return replace(outcome, status="FILLED"), fill


def simulate(
    dataset: Dataset,
    initial_capital: Decimal,
    strategy: StrategyConfig | None = None,
    settings: ExecutionSettings | None = None,
) -> SimulationResult:
    """Run a built-in rule through the existing next-open execution/accounting loop."""
    if settings is None:
        settings = ExecutionSettings()
    if not isinstance(settings, ExecutionSettings):
        raise SimulationError("settings must be ExecutionSettings.")
    if strategy is None:
        strategy = BuyAndHold()
    try:
        rule = create_rule(strategy, sell_after_session=settings.sell_after_session)
    except StrategyError as exc:
        raise SimulationError(str(exc)) from exc
    # Isolate precision, rounding, exponent limits and traps from the caller's context.
    with localcontext(ARITHMETIC):
        bars, warmup = _preflight(dataset, initial_capital, settings)
        for bar in warmup:
            rule.on_close(bar.date, bar.close, 0)  # Discard targets; portfolio does not exist yet.
        cash = initial_capital.quantize(CENT)
        shares = 0
        basis = realized = Decimal("0.00")
        orders: list[Order] = []
        fills: list[Fill] = []
        valuations: list[DailyValuation] = []
        decisions: list[Decision] = []
        pending: Order | None = None
        for index, bar in enumerate(bars):
            if pending is not None:
                outcome, fill = _execute(pending, bar, cash, shares, settings)
                orders[-1] = outcome
                pending = None
                if fill is not None:
                    cash += fill.cash_change
                    if fill.side == "BUY":
                        shares = fill.quantity
                        basis = -fill.cash_change
                    else:
                        realized += fill.cash_change - basis
                        shares = 0
                        basis = Decimal("0.00")
                    fills.append(fill)
            if cash < 0 or type(shares) is not int or shares < 0:
                raise SimulationError("Nonnegative cash/integer-share invariant failed.")
            if cash > MAX_CASH or shares > MAX_SHARES:
                raise SimulationError("Portfolio exceeds the supported precision-28 range.")
            marked = shares * bar.close
            equity = cash + marked
            valuations.append(DailyValuation(
                session=bar.date, cash=cash, shares=shares, close=bar.close,
                market_value=marked, equity=equity, cost_basis=basis,
                realized_pnl=realized, unrealized_pnl=marked - basis,
            ))
            target = rule.on_close(bar.date, bar.close, shares)
            decisions.append(Decision(bar.date, target, cash, shares))
            if (target == "LONG" and shares == 0) or (target == "FLAT" and shares > 0):
                eligible = bars[index + 1].date if index + 1 < len(bars) else None
                pending = Order(
                    order_id=len(orders) + 1, decision_session=bar.date,
                    eligible_session=eligible, target=target,
                    side="BUY" if target == "LONG" else "SELL",
                    budget=cash if target == "LONG" else None,
                    requested_shares=shares if target == "FLAT" else None,
                )
                if eligible is None:
                    orders.append(replace(pending, status="EXPIRED", outcome_session=bar.date, reason="end_of_window"))
                    pending = None
                else:
                    orders.append(pending)
        final = valuations[-1]
        warnings = dataset.report.warnings + (
            "Next observed session is a proxy for next tradable session; coverage and opening liquidity remain unverified.",
            "Split declarations cover the supplied dataset interval; no event is bypassed by selecting a subwindow.",
        )
        if settings.sell_after_session:
            warnings += ("Diagnostic single-exit behavior enabled; this is not the buy-and-hold benchmark.",)
        if warmup:
            warnings += ("Only indicators consume the recorded prior warm-up interval; evaluation starts flat with fresh cash and no pending order.",)
        return SimulationResult(
            engine_version=ENGINE_VERSION, dataset_id=dataset.report.dataset_id,
            source_sha256=dataset.report.source_sha256, metadata_sha256=dataset.report.metadata_sha256,
            metadata=dataset.metadata, start_date=bars[0].date, end_date=bars[-1].date,
            initial_capital=initial_capital.quantize(CENT), settings=settings, strategy=strategy,
            final_cash=cash, final_shares=shares, final_equity=final.equity,
            realized_pnl=final.realized_pnl, unrealized_pnl=final.unrealized_pnl,
            valuations=tuple(valuations), decisions=tuple(decisions), orders=tuple(orders),
            fills=tuple(fills), assumptions=ASSUMPTIONS, warnings=warnings,
            warmup_start=warmup[0].date if warmup else None,
            warmup_end=warmup[-1].date if warmup else None, warmup_bars=len(warmup),
        )


def simulate_buy_and_hold(
    dataset: Dataset,
    initial_capital: Decimal,
    settings: ExecutionSettings | None = None,
) -> SimulationResult:
    """Compatibility entry point, including the original optional diagnostic exit."""
    return simulate(dataset, initial_capital, BuyAndHold(), settings)
