"""Independent Decimal reconciliation; never call engine execution/cost helpers."""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from quantlab.data import Bar
from quantlab.execution import ExecutionSettings, SimulationResult

from .models import Evidence, Finding, checked, finite, unavailable, whole

CENT = Decimal("0.01")
UNIT = Decimal("0.000001")


def check_balances(result: SimulationResult) -> Finding:
    problems = []
    if not whole(result.final_shares) or not all(finite(n) for n in (result.final_cash, result.final_equity, result.realized_pnl, result.unrealized_pnl)):
        problems.append(Evidence("result.final_state", repr((result.final_cash, result.final_shares, result.final_equity)), "finite Decimal final balances and nonnegative integer shares"))
    previous = None
    for i, value in enumerate(result.valuations):
        ref = f"valuations[{i}]"
        if type(value.session) is not date or (previous is not None and value.session <= previous):
            problems.append(Evidence(ref + ".session", repr(value.session), "strictly increasing dates"))
        else:
            previous = value.session
        money = (value.cash, value.close, value.market_value, value.equity, value.cost_basis, value.realized_pnl, value.unrealized_pnl)
        if not all(finite(number) for number in money) or not whole(value.shares):
            problems.append(Evidence(ref, repr(value), "finite Decimal values and nonnegative integer shares"))
            continue
        if value.cash < 0 or value.cash != value.cash.quantize(CENT) or value.cost_basis < 0:
            problems.append(Evidence(ref + ".cash/basis", repr((value.cash, value.cost_basis)), "nonnegative cents cash and nonnegative basis"))
        if value.close <= 0 or value.market_value != value.shares * value.close or value.equity != value.cash + value.market_value:
            problems.append(Evidence(ref + ".equity", repr((value.close, value.market_value, value.equity)), "positive close; mark=shares*close; equity=cash+mark"))
        if value.unrealized_pnl != value.market_value - value.cost_basis:
            problems.append(Evidence(ref + ".unrealized_pnl", str(value.unrealized_pnl), str(value.market_value - value.cost_basis)))
    if not result.valuations:
        problems.append(Evidence("valuations", "empty", "terminal valuation"))
    else:
        final = result.valuations[-1]
        for field, recorded in (("cash", result.final_cash), ("shares", result.final_shares), ("equity", result.final_equity), ("realized_pnl", result.realized_pnl), ("unrealized_pnl", result.unrealized_pnl)):
            if recorded != getattr(final, field):
                problems.append(Evidence("result.final_" + field, repr(recorded), repr(getattr(final, field))))
    return checked("ACCOUNTING.BALANCES", "Portfolio balances and terminal state", problems,
                   "Checked nonnegative cents cash/integer holdings, exact mark/equity/unrealized P&L, and terminal equality.")


def check_ledger(result: SimulationResult) -> Finding:
    if not finite(result.initial_capital) or result.initial_capital <= 0 or result.initial_capital != result.initial_capital.quantize(CENT):
        return checked("ACCOUNTING.LEDGER", "Cash and position ledger", [Evidence("initial_capital", repr(result.initial_capital), "positive Decimal cents")], "Initial flat cash ledger is invalid.")
    problems = []
    by_session = defaultdict(list)
    for i, fill in enumerate(result.fills):
        if type(fill.session) is not date or not whole(fill.quantity, 1) or fill.side not in ("BUY", "SELL") or not all(finite(n) for n in (fill.notional, fill.fee, fill.cash_change)):
            return checked("ACCOUNTING.LEDGER", "Cash and position ledger", [Evidence(f"fills[{i}]", repr(fill), "valid dates, side, quantity and finite money", fill_index=i)], "Malformed fill prevents reconciliation.")
        by_session[fill.session].append((i, fill))
    orders = {o.order_id: o for o in result.orders if whole(o.order_id, 1)}
    cash, shares, basis, realized = result.initial_capital, 0, Decimal("0.00"), Decimal("0.00")
    for i, value in enumerate(result.valuations):
        if type(value.session) is not date:
            problems.append(Evidence(f"valuations[{i}].session", repr(value.session), "date for reconciliation"))
            continue
        linked = by_session.pop(value.session, [])
        if len(linked) > 1:
            problems.append(Evidence(f"valuations[{i}].fills", str(len(linked)), "at most one eligible fill per session", session=value.session))
        for fill_index, fill in linked:
            order = orders.get(fill.order_id) if whole(fill.order_id, 1) else None
            if fill.side == "BUY":
                if shares != 0:
                    problems.append(Evidence(f"fills[{fill_index}].BUY", str(shares), "flat position before entry", fill.order_id, fill_index))
                debit = fill.notional + fill.fee
                if order is None or not finite(order.budget) or order.budget != cash or debit > cash:
                    problems.append(Evidence(f"fills[{fill_index}].budget", repr(order.budget if order else None), f"available cash {cash}; debit {debit} affordable", fill.order_id, fill_index))
                cash -= debit
                shares = fill.quantity
                basis = debit
            else:
                if shares != fill.quantity or shares <= 0:
                    problems.append(Evidence(f"fills[{fill_index}].SELL", str(fill.quantity), f"entire current position {shares}", fill.order_id, fill_index))
                credit = fill.notional - fill.fee
                if credit < 0:
                    problems.append(Evidence(f"fills[{fill_index}].credit", str(credit), "sale proceeds cover fee", fill.order_id, fill_index))
                cash += credit
                realized += credit - basis
                shares, basis = 0, Decimal("0.00")
        expected = (cash, shares, basis, realized)
        recorded = (value.cash, value.shares, value.cost_basis, value.realized_pnl)
        if recorded != expected:
            problems.append(Evidence(f"valuations[{i}].ledger", repr(recorded), repr(expected), session=value.session))
    for session, linked in by_session.items():
        problems.append(Evidence("fills.session", str(session), "a recorded valuation session", fill_index=linked[0][0], session=session))
    valuations = {v.session: v for v in result.valuations if type(v.session) is date}
    for i, decision in enumerate(result.decisions):
        value = valuations.get(decision.session) if type(decision.session) is date else None
        if value is None or (decision.cash, decision.shares) != (value.cash, value.shares):
            problems.append(Evidence(f"decisions[{i}].position", repr((decision.cash, decision.shares)), "matching closing cash and shares"))
    return checked("ACCOUNTING.LEDGER", "Cash and position ledger", problems,
                   "Folded recorded full fills from initial flat cash using notional plus/minus fee; reconciled each close and decision state, without generating signals/orders.")


def check_cost_configuration(result: SimulationResult) -> Finding:
    problems = []
    if not isinstance(result.settings, ExecutionSettings):
        problems.append(Evidence("settings", repr(result.settings), "retained ExecutionSettings"))
    else:
        for field, maximum in (("commission_per_fill_usd", Decimal("999999999999999999999.99")), ("slippage_bps", Decimal("9999.999999"))):
            number = getattr(result.settings, field)
            if not finite(number) or number < 0 or number > maximum or number != number.quantize(UNIT):
                problems.append(Evidence("settings." + field, repr(number), f"finite Decimal 0..{maximum}, at most six fractional places"))
    return checked("COSTS.CONFIGURATION", "Retained supported cost settings", problems,
                   "Checked presence, finite nonnegative Decimal, precision and supported commission/bps ranges; this does not establish the original request.")


def check_fill_costs(result: SimulationResult, configuration: Finding) -> Finding:
    if result.engine_version not in ("1.2.0", "1.3.0") or configuration.status != "PASS":
        return unavailable("COSTS.FILL_MATH", "Declared cost arithmetic", "Requires supported engine 1.2.0/1.3.0 and valid retained cost configuration.")
    problems = []
    fee = result.settings.commission_per_fill_usd.quantize(CENT)
    fraction = result.settings.slippage_bps / Decimal("10000")
    for i, fill in enumerate(result.fills):
        ref = f"fills[{i}]"
        if not whole(fill.quantity, 1) or fill.side not in ("BUY", "SELL") or not all(finite(n) for n in (fill.base_open, fill.effective_price, fill.notional, fill.fee, fill.cash_change)):
            problems.append(Evidence(ref, repr(fill), "valid fill quantities/side and finite Decimal money", fill_index=i))
            continue
        price = (fill.base_open * (1 + fraction if fill.side == "BUY" else 1 - fraction)).quantize(UNIT)
        notional = (fill.quantity * price).quantize(CENT)
        change = -(notional + fee) if fill.side == "BUY" else notional - fee
        expected = (price, notional, fee, change)
        recorded = (fill.effective_price, fill.notional, fill.fee, fill.cash_change)
        if fill.base_open <= 0 or price <= 0 or recorded != expected or (fill.side == "SELL" and change < 0):
            problems.append(Evidence(ref + ".money", repr(recorded), repr(expected) + "; positive prices and fee-covering sale", fill.order_id, i, fill.session if type(fill.session) is date else None))
    return checked("COSTS.FILL_MATH", "Declared cost arithmetic", problems,
                   "Independently applied six-decimal slipped prices and cents notional/fees with precision 28/ROUND_HALF_UP to recorded base opens; no production cost helper called.")


def check_source_prices(result: SimulationResult, bars: tuple[Bar, ...] | None) -> Finding:
    if bars is None:
        return unavailable("DATA.PRICE_REFERENCES", "Execution and mark source references", "No usable source bars; base opens, closing marks and execution volume cannot be independently compared.")
    source = {bar.date: bar for bar in bars}
    problems = []
    for i, fill in enumerate(result.fills):
        bar = source.get(fill.session) if type(fill.session) is date else None
        if bar is None or fill.base_open != bar.open or bar.volume == 0:
            problems.append(Evidence(f"fills[{i}].base_open", repr(fill.base_open), repr((bar.open, bar.volume)) if bar else "observed source session", fill.order_id, i))
    for i, value in enumerate(result.valuations):
        bar = source.get(value.session) if type(value.session) is date else None
        if bar is None or value.close != bar.close:
            problems.append(Evidence(f"valuations[{i}].close", repr(value.close), repr(bar.close) if bar else "observed source close"))
    for i, order in enumerate(result.orders):
        if order.status == "EXPIRED":
            continue
        bar = source.get(order.outcome_session) if type(order.outcome_session) is date else None
        if bar is None or order.base_open != bar.open:
            problems.append(Evidence(f"orders[{i}].base_open", repr(order.base_open), repr(bar.open) if bar else "observed attempted execution open", order.order_id))
    return checked("DATA.PRICE_REFERENCES", "Execution and mark source references", problems,
                   "Compared attempted/filled opens and closing marks with supplied source bars; positive daily volume does not prove opening liquidity.")
