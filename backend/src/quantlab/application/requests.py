"""Pydantic validation at HTTP and saved-request boundaries, not financial logic."""

from datetime import date
from decimal import Decimal, InvalidOperation
import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, StrictBool, StrictInt, StringConstraints, field_validator, model_validator

from quantlab.execution import ExecutionSettings
from quantlab.experiments import CostScenario, EvaluationPeriod
from quantlab.strategies import BuyAndHold, SMACrossover, TimeSeriesMomentum

MAX_METADATA_BYTES = 64 * 1024
MAX_CONFIGURATION_BYTES = 64 * 1024


def _decimal_text(value: str) -> str:
    if not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value):
        raise ValueError("Use a plain decimal string without exponent notation.")
    try:
        if not Decimal(value).is_finite():
            raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError("Expected a finite Decimal encoded as a string.") from None
    return value


def _date(value):
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return date.fromisoformat(value)
    if type(value) is date:
        return value
    raise ValueError("Expected an ISO YYYY-MM-DD date string.")


DecimalText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=128), AfterValidator(_decimal_text)]
DateValue = Annotated[date, BeforeValidator(_date)]
DatasetId = Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9a-f]{64}$")]


class BoundaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_default=True)


class DatasetImport(BoundaryModel):
    csv_text: str
    metadata: dict[str, object]


class BuyHoldRequest(BoundaryModel):
    kind: Literal["buy_and_hold"]

    def domain(self):
        return BuyAndHold()


class SMARequest(BoundaryModel):
    kind: Literal["sma"]
    fast_window: StrictInt
    slow_window: StrictInt

    def domain(self):
        return SMACrossover(self.fast_window, self.slow_window)

    @model_validator(mode="after")
    def supported(self):
        self.domain()
        return self


class MomentumRequest(BoundaryModel):
    kind: Literal["momentum"]
    lookback: StrictInt
    threshold: DecimalText = "0"

    def domain(self):
        return TimeSeriesMomentum(self.lookback, Decimal(self.threshold))

    @model_validator(mode="after")
    def supported(self):
        self.domain()
        return self


StrategyRequest = Annotated[BuyHoldRequest | SMARequest | MomentumRequest, Field(discriminator="kind")]


class PeriodRequest(BoundaryModel):
    start_date: DateValue
    end_date: DateValue

    def domain(self):
        return EvaluationPeriod(self.start_date, self.end_date)

    @model_validator(mode="after")
    def ordered(self):
        self.domain()
        return self


class CostRequest(BoundaryModel):
    commission_per_fill_usd: DecimalText = "0.00"
    slippage_bps: DecimalText = "0"

    def domain(self):
        return CostScenario(Decimal(self.commission_per_fill_usd), Decimal(self.slippage_bps))


class SettingsRequest(CostRequest):
    acknowledge_unverified_coverage: StrictBool = False

    def domain(self):
        return ExecutionSettings(commission_per_fill_usd=Decimal(self.commission_per_fill_usd),
                                 slippage_bps=Decimal(self.slippage_bps),
                                 acknowledge_unverified_coverage=self.acknowledge_unverified_coverage)


class ExperimentRequest(BoundaryModel):
    request_version: Literal[1] = 1
    dataset_id: DatasetId
    mode: Literal["backtest", "grid", "train_test"] = "backtest"
    initial_capital: DecimalText
    configurations: Annotated[list[StrategyRequest], Field(min_length=1, max_length=100)]
    settings: SettingsRequest = Field(default_factory=SettingsRequest)
    periods: Annotated[list[PeriodRequest], Field(min_length=1)] | None = None
    costs: Annotated[list[CostRequest], Field(min_length=1)] | None = None
    training_period: PeriodRequest | None = None
    test_period: PeriodRequest | None = None
    warmup: StrictBool = True
    include_benchmark: StrictBool = True
    annual_risk_free_rate: DecimalText = "0"

    @field_validator("request_version", mode="before")
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError("request_version must be integer 1, not bool/float.")
        return value

    @model_validator(mode="after")
    def mode_fields(self):
        if self.mode == "train_test":
            if self.training_period is None or self.test_period is None or self.periods is not None or self.costs is not None:
                raise ValueError("train_test requires training_period/test_period and fixed settings costs, without periods/costs lists.")
        else:
            if self.training_period is not None or self.test_period is not None or self.warmup is not True:
                raise ValueError("Training/test fields and warmup option belong to train_test only.")
            if self.mode == "backtest" and (len(self.configurations) != 1 or (self.periods and len(self.periods) != 1) or (self.costs and len(self.costs) != 1)):
                raise ValueError("backtest requires one configuration and at most one period/cost; use grid for comparisons.")
        return self

    def arguments(self) -> dict:
        result = dict(initial_capital=Decimal(self.initial_capital),
                      configurations=tuple(config.domain() for config in self.configurations),
                      settings=self.settings.domain(), include_benchmark=self.include_benchmark,
                      annual_risk_free_rate=Decimal(self.annual_risk_free_rate))
        if self.mode == "train_test":
            result.update(training_period=self.training_period.domain(), test_period=self.test_period.domain(), warmup=self.warmup)
        else:
            result.update(periods=tuple(period.domain() for period in self.periods) if self.periods else None,
                          costs=tuple(cost.domain() for cost in self.costs) if self.costs else None)
        return result
