"""Modelos de dados para o framework de investimentos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class Sector(str, Enum):
    TECHNOLOGY = "Tecnologia"
    FINANCE = "Finanças"
    HEALTHCARE = "Saúde"
    ENERGY = "Energia"
    CONSUMER = "Consumo"
    INDUSTRIAL = "Industrial"
    MATERIALS = "Materiais"
    UTILITIES = "Utilidades"
    REAL_ESTATE = "Imobiliário"
    COMMUNICATION = "Comunicação"
    OTHER = "Outro"


class RiskLevel(str, Enum):
    VERY_LOW = "Muito Baixo"
    LOW = "Baixo"
    MODERATE = "Moderado"
    HIGH = "Alto"
    VERY_HIGH = "Muito Alto"


class Recommendation(str, Enum):
    STRONG_BUY = "Compra Forte"
    BUY = "Compra"
    HOLD = "Manter"
    SELL = "Venda"
    STRONG_SELL = "Venda Forte"


@dataclass
class FinancialData:
    """Dados financeiros fundamentalistas de uma empresa."""

    revenue: float | None = None
    net_income: float | None = None
    ebitda: float | None = None
    total_debt: float | None = None
    total_cash: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    free_cash_flow: float | None = None
    operating_margin: float | None = None
    profit_margin: float | None = None
    roe: float | None = None
    roa: float | None = None
    current_ratio: float | None = None
    debt_to_equity: float | None = None
    dividend_yield: float | None = None
    payout_ratio: float | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ValuationMetrics:
    """Métricas de valuation."""

    pe_ratio: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    pb_ratio: float | None = None
    ps_ratio: float | None = None
    ev_ebitda: float | None = None
    ev_revenue: float | None = None
    market_cap: float | None = None
    enterprise_value: float | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class TechnicalIndicators:
    """Indicadores de análise técnica."""

    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    ema_12: float | None = None
    ema_26: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None
    atr_14: float | None = None
    volume_avg_20: float | None = None
    price_change_1d: float | None = None
    price_change_5d: float | None = None
    price_change_1m: float | None = None
    price_change_3m: float | None = None
    price_change_6m: float | None = None
    price_change_1y: float | None = None
    volatility_30d: float | None = None
    beta: float | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class CompanyProfile:
    """Perfil completo de uma empresa."""

    ticker: str
    name: str = ""
    sector: Sector = Sector.OTHER
    industry: str = ""
    country: str = ""
    currency: str = "USD"
    description: str = ""
    website: str = ""
    employees: int | None = None
    current_price: float | None = None
    target_price: float | None = None
    financials: FinancialData = field(default_factory=FinancialData)
    valuation: ValuationMetrics = field(default_factory=ValuationMetrics)
    technicals: TechnicalIndicators = field(default_factory=TechnicalIndicators)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AnalysisResult:
    """Resultado consolidado de análise de uma empresa."""

    ticker: str
    company_name: str
    date: date = field(default_factory=date.today)
    fundamental_score: float = 0.0  # 0-100
    technical_score: float = 0.0  # 0-100
    valuation_score: float = 0.0  # 0-100
    overall_score: float = 0.0  # 0-100
    risk_level: RiskLevel = RiskLevel.MODERATE
    recommendation: Recommendation = Recommendation.HOLD
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    key_metrics: dict = field(default_factory=dict)
    summary: str = ""

    def to_report_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "empresa": self.company_name,
            "data": self.date.isoformat(),
            "score_fundamentalista": round(self.fundamental_score, 1),
            "score_tecnico": round(self.technical_score, 1),
            "score_valuation": round(self.valuation_score, 1),
            "score_geral": round(self.overall_score, 1),
            "risco": self.risk_level.value,
            "recomendacao": self.recommendation.value,
            "pontos_fortes": self.strengths,
            "pontos_fracos": self.weaknesses,
            "metricas_chave": self.key_metrics,
            "resumo": self.summary,
        }


@dataclass
class PortfolioPosition:
    """Posição de um ativo na carteira."""

    ticker: str
    company_name: str
    shares: float
    avg_cost: float
    current_price: float = 0.0
    sector: Sector = Sector.OTHER

    @property
    def total_cost(self) -> float:
        return self.shares * self.avg_cost

    @property
    def current_value(self) -> float:
        return self.shares * self.current_price

    @property
    def gain_loss(self) -> float:
        return self.current_value - self.total_cost

    @property
    def gain_loss_pct(self) -> float:
        if self.total_cost == 0:
            return 0.0
        return (self.gain_loss / self.total_cost) * 100


@dataclass
class Portfolio:
    """Carteira de investimentos."""

    name: str
    positions: list[PortfolioPosition] = field(default_factory=list)
    cash: float = 0.0

    @property
    def total_invested(self) -> float:
        return sum(p.total_cost for p in self.positions)

    @property
    def total_value(self) -> float:
        return sum(p.current_value for p in self.positions) + self.cash

    @property
    def total_gain_loss(self) -> float:
        return sum(p.gain_loss for p in self.positions)

    @property
    def total_gain_loss_pct(self) -> float:
        invested = self.total_invested
        if invested == 0:
            return 0.0
        return (self.total_gain_loss / invested) * 100

    def sector_allocation(self) -> dict[str, float]:
        total = self.total_value
        if total == 0:
            return {}
        allocation: dict[str, float] = {}
        for pos in self.positions:
            sector = pos.sector.value
            allocation[sector] = allocation.get(sector, 0) + pos.current_value
        return {k: round(v / total * 100, 2) for k, v in allocation.items()}

    def add_position(self, position: PortfolioPosition) -> None:
        for existing in self.positions:
            if existing.ticker == position.ticker:
                total_shares = existing.shares + position.shares
                total_cost = existing.total_cost + position.total_cost
                existing.shares = total_shares
                existing.avg_cost = total_cost / total_shares if total_shares else 0
                return
        self.positions.append(position)

    def remove_position(self, ticker: str, shares: float | None = None) -> None:
        for i, pos in enumerate(self.positions):
            if pos.ticker == ticker:
                if shares is None or shares >= pos.shares:
                    self.positions.pop(i)
                else:
                    pos.shares -= shares
                return
