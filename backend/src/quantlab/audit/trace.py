"""Observed-session timing and order/fill lifecycle checks, without strategy execution."""

from collections import defaultdict
from datetime import date

from quantlab.data import Bar
from quantlab.execution import SimulationResult

from .models import Evidence, Finding, checked, finite, unavailable, whole


def check_lifecycle(result: SimulationResult) -> Finding:
    problems = []
    orders = {}
    decisions = {}
    for i, decision in enumerate(result.decisions):
        if decision.target not in ("LONG", "FLAT", "HOLD"):
            problems.append(Evidence(f"decisions[{i}].target", repr(decision.target), "LONG, FLAT or HOLD"))
        if not finite(decision.cash) or not whole(decision.shares):
            problems.append(Evidence(f"decisions[{i}].state", repr((decision.cash, decision.shares)), "finite Decimal cash and nonnegative integer shares"))
        if type(decision.session) is not date or decision.session in decisions:
            problems.append(Evidence(f"decisions[{i}].session", repr(decision.session), "unique date"))
        else:
            decisions[decision.session] = decision
    fills = defaultdict(list)
    for i, fill in enumerate(result.fills):
        if not whole(fill.order_id, 1):
            problems.append(Evidence(f"fills[{i}].order_id", repr(fill.order_id), "positive integer", fill_index=i))
            continue
        fills[fill.order_id].append((i, fill))
        if not whole(fill.quantity, 1):
            problems.append(Evidence(f"fills[{i}].quantity", repr(fill.quantity), "positive integer", fill.order_id, i))
    for i, order in enumerate(result.orders):
        ref = f"orders[{i}]"
        if not whole(order.order_id, 1) or order.order_id in orders or order.order_id != i + 1:
            problems.append(Evidence(ref + ".order_id", repr(order.order_id), f"unique sequential ID {i + 1}"))
        if not whole(order.order_id, 1):
            continue
        orders[order.order_id] = order
        linked = fills.get(order.order_id, [])
        if order.status not in ("FILLED", "REJECTED", "EXPIRED"):
            problems.append(Evidence(ref + ".status", repr(order.status), "terminal FILLED/REJECTED/EXPIRED", order.order_id))
        if len(linked) != (1 if order.status == "FILLED" else 0):
            problems.append(Evidence(ref + ".fills", str(len(linked)), "one for FILLED, zero otherwise", order.order_id))
        decision = decisions.get(order.decision_session) if type(order.decision_session) is date else None
        if decision is None or decision.target != order.target or (order.target, order.side) not in (("LONG", "BUY"), ("FLAT", "SELL")):
            problems.append(Evidence(ref + ".decision", repr((order.decision_session, order.target, order.side)), "matching LONG/BUY or FLAT/SELL close decision", order.order_id))
        elif order.side == "BUY":
            if (not finite(decision.cash) or decision.shares != 0 or order.requested_shares is not None
                    or not finite(order.budget) or order.budget != decision.cash):
                problems.append(Evidence(ref + ".budget", repr(order.budget), "flat decision's available cash, no precommitted quantity", order.order_id))
        elif order.budget is not None or not whole(order.requested_shares, 1) or order.requested_shares != decision.shares:
            problems.append(Evidence(ref + ".requested_shares", repr(order.requested_shares), "full positive decision position, no buy budget", order.order_id))
        if order.status == "FILLED" and order.reason is not None:
            problems.append(Evidence(ref + ".reason", repr(order.reason), "None for filled order", order.order_id))
        if order.status == "REJECTED" and (not isinstance(order.reason, str) or not order.reason.strip()):
            problems.append(Evidence(ref + ".reason", repr(order.reason), "recorded rejection reason", order.order_id))
        if order.status == "EXPIRED" and (order.reason != "end_of_window" or order.base_open is not None or order.effective_price is not None):
            problems.append(Evidence(ref + ".expiry", repr((order.reason, order.base_open, order.effective_price)), "end_of_window without attempted prices", order.order_id))
        for index, fill in linked:
            prices = (fill.base_open, fill.effective_price, order.base_open, order.effective_price)
            if not all(finite(number) for number in prices) or (fill.side, fill.session, fill.base_open, fill.effective_price) != (order.side, order.outcome_session, order.base_open, order.effective_price):
                problems.append(Evidence(f"fills[{index}]", repr(fill), "side/session/prices agree with linked order", order.order_id, index))
    for order_id, linked in fills.items():
        if order_id not in orders:
            problems.append(Evidence("fills.order_id", str(order_id), "existing order", order_id))
        if len(linked) > 1:
            problems.append(Evidence("fills.association", str(len(linked)), "at most one fill per order", order_id))
    return checked("ORDERS.LIFECYCLE", "Order and fill lifecycle", problems,
                   f"Checked {len(result.orders)} orders/{len(result.fills)} fills and their recorded decisions; no event history is inferred.")


def check_causality(result: SimulationResult) -> Finding:
    problems = []
    orders = {order.order_id: order for order in result.orders if whole(order.order_id, 1)}
    previous = None
    for i, decision in enumerate(result.decisions):
        if type(decision.session) is not date or (previous is not None and decision.session <= previous):
            problems.append(Evidence(f"decisions[{i}].session", repr(decision.session), "strictly increasing recorded close decisions"))
        else:
            previous = decision.session
    previous = None
    for i, order in enumerate(result.orders):
        if type(order.decision_session) is not date or type(order.outcome_session) is not date:
            problems.append(Evidence(f"orders[{i}].sessions", repr((order.decision_session, order.outcome_session)), "decision and terminal outcome dates"))
        elif order.status == "EXPIRED":
            if order.outcome_session != order.decision_session or order.decision_session != result.end_date or order.eligible_session is not None:
                problems.append(Evidence(f"orders[{i}].expiry_session", repr((order.decision_session, order.outcome_session, order.eligible_session)), "final-close decision and expiry, without eligible session", order.order_id))
        elif order.status != "EXPIRED" and order.outcome_session <= order.decision_session:
            problems.append(Evidence(f"orders[{i}].outcome_session", str(order.outcome_session), "strictly after decision close", order.order_id))
        if type(order.decision_session) is date:
            if previous is not None and order.decision_session <= previous:
                problems.append(Evidence(f"orders[{i}].decision_session", str(order.decision_session), "strictly increasing order decisions", order.order_id))
            previous = order.decision_session
    previous = None
    for i, fill in enumerate(result.fills):
        order = orders.get(fill.order_id) if whole(fill.order_id, 1) else None
        if order is None or type(fill.session) is not date or type(order.decision_session) is not date:
            problems.append(Evidence(f"fills[{i}].session", repr(fill.session), "linked order and valid session dates", fill_index=i))
        elif fill.session <= order.decision_session or fill.session != order.eligible_session:
            problems.append(Evidence(f"fills[{i}].session", str(fill.session), f"after {order.decision_session}, at declared eligibility {order.eligible_session}", order.order_id, i, fill.session))
        if type(fill.session) is date:
            if previous is not None and fill.session <= previous:
                problems.append(Evidence(f"fills[{i}].session", str(fill.session), "strictly increasing fill history", fill.order_id, i, fill.session))
            previous = fill.session
    return checked("TIMING.CAUSALITY", "Recorded decision precedes execution", problems,
                   "Checked recorded decision/outcome/eligibility chronology only; this is not proof against arbitrary strategy look-ahead.")


def check_sessions(result: SimulationResult, bars: tuple[Bar, ...] | None) -> Finding:
    if bars is None:
        return unavailable("TIMING.NEXT_SESSION", "Next observed session", "No usable source bars supplied; recorded eligibility cannot be independently checked against observed sessions.")
    positions = {bar.date: i for i, bar in enumerate(bars)}
    sessions = tuple(bar.date for bar in bars)
    problems = []
    if (tuple(v.session for v in result.valuations) != sessions
            or tuple(d.session for d in result.decisions) != sessions
            or not sessions or (result.start_date, result.end_date) != (sessions[0], sessions[-1])):
        problems.append(Evidence("result.evaluation_sessions", repr((result.start_date, result.end_date, len(result.valuations), len(result.decisions))), "exact selected source session sequence"))
    for i, order in enumerate(result.orders):
        index = positions.get(order.decision_session) if type(order.decision_session) is date else None
        if index is None:
            problems.append(Evidence(f"orders[{i}].decision_session", repr(order.decision_session), "observed selected source session", order.order_id))
            continue
        next_session = sessions[index + 1] if index + 1 < len(sessions) else None
        expected_outcome = next_session if next_session is not None else sessions[-1]
        if (order.eligible_session != next_session or order.outcome_session != expected_outcome
                or (next_session is None) != (order.status == "EXPIRED")):
            problems.append(Evidence(f"orders[{i}].eligibility", repr((order.eligible_session, order.outcome_session, order.status)), f"next observed {next_session}; final-close intents expire", order.order_id))
    return checked("TIMING.NEXT_SESSION", "Next observed session", problems,
                   "Compared against selected source dates, not next-calendar-day arithmetic; source completeness remains unverified.")


def check_warmup(result: SimulationResult, source: tuple[Bar, ...] | None) -> Finding:
    rule, title = "TIMING.WARMUP", "Indicator-only warm-up boundaries"
    start = getattr(result.settings, "warmup_start_date", None)
    end = getattr(result.settings, "warmup_end_date", None)
    if start is None and end is None:
        problems = [] if (result.warmup_start, result.warmup_end, result.warmup_bars) == (None, None, 0) and whole(result.warmup_bars) else [Evidence("result.warmup", repr((result.warmup_start, result.warmup_end, result.warmup_bars)), "no warm-up metadata without requested history")]
        return checked(rule, title, problems, "No indicator-only warm-up was requested.")
    evaluation_start = getattr(result.settings, "start_date", None)
    if (type(start) is not date or type(end) is not date or type(evaluation_start) is not date
            or type(result.start_date) is not date or not start <= end < evaluation_start <= result.start_date):
        return checked(rule, title, [Evidence("settings.warmup", repr((start, end)), "ordered warm-up strictly before evaluation")], "Warm-up date contract is invalid.")
    if source is None:
        return unavailable(rule, title, "Source bars are needed to check observed warm-up bounds/count; recorded-ledger checks still apply.")
    history = tuple(bar for bar in source if start <= bar.date <= end)
    expected = (history[0].date, history[-1].date, len(history)) if history else (None, None, 0)
    observed = (result.warmup_start, result.warmup_end, result.warmup_bars)
    problems = [] if history and observed == expected and whole(result.warmup_bars, 1) else [Evidence("result.warmup", repr(observed), repr(expected))]
    for name in ("decisions", "fills", "valuations"):
        if any(item.session < result.start_date for item in getattr(result, name) if type(item.session) is date):
            problems.append(Evidence("result." + name, "pre-evaluation record", "warm-up produces no orders/fills/decisions/valuations"))
    if any(order.decision_session < result.start_date for order in result.orders if type(order.decision_session) is date):
        problems.append(Evidence("result.orders", "pre-evaluation order", "no warm-up order"))
    return checked(rule, title, problems, "Compared warm-up source bounds/count and absence of pre-evaluation trading/valuation records; ledger rule independently starts from fresh flat cash.")
