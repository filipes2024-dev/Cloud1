"""Provedor de dados de mercado usando yfinance."""

from __future__ import annotations

import logging
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

from .models import (
    CompanyProfile,
    FinancialData,
    Sector,
    TechnicalIndicators,
    ValuationMetrics,
)

logger = logging.getLogger(__name__)

_SECTOR_MAP = {
    "Technology": Sector.TECHNOLOGY,
    "Financial Services": Sector.FINANCE,
    "Healthcare": Sector.HEALTHCARE,
    "Energy": Sector.ENERGY,
    "Consumer Cyclical": Sector.CONSUMER,
    "Consumer Defensive": Sector.CONSUMER,
    "Industrials": Sector.INDUSTRIAL,
    "Basic Materials": Sector.MATERIALS,
    "Utilities": Sector.UTILITIES,
    "Real Estate": Sector.REAL_ESTATE,
    "Communication Services": Sector.COMMUNICATION,
}


def _safe_get(info: dict, key: str, default=None):
    val = info.get(key, default)
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return val


class MarketDataProvider:
    """Busca dados de mercado via yfinance."""

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        """Busca perfil completo de uma empresa."""
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            raise ValueError(f"Ticker '{ticker}' nao encontrado ou sem dados disponiveis.")

        sector_str = _safe_get(info, "sector", "")
        sector = _SECTOR_MAP.get(sector_str, Sector.OTHER)

        financials = self._extract_financials(info)
        valuation = self._extract_valuation(info)
        technicals = self._compute_technicals(stock)

        price = _safe_get(info, "currentPrice") or _safe_get(info, "regularMarketPrice", 0)

        return CompanyProfile(
            ticker=ticker.upper(),
            name=_safe_get(info, "longName", ticker),
            sector=sector,
            industry=_safe_get(info, "industry", ""),
            country=_safe_get(info, "country", ""),
            currency=_safe_get(info, "currency", "USD"),
            description=_safe_get(info, "longBusinessSummary", ""),
            website=_safe_get(info, "website", ""),
            employees=_safe_get(info, "fullTimeEmployees"),
            current_price=price,
            target_price=_safe_get(info, "targetMeanPrice"),
            financials=financials,
            valuation=valuation,
            technicals=technicals,
            last_updated=datetime.now(),
        )

    def get_historical_prices(
        self, ticker: str, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame:
        """Retorna historico de precos."""
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        if hist.empty:
            raise ValueError(f"Sem dados historicos para '{ticker}'.")
        return hist

    def get_multiple_profiles(self, tickers: list[str]) -> dict[str, CompanyProfile]:
        """Busca perfis de multiplas empresas."""
        profiles: dict[str, CompanyProfile] = {}
        for ticker in tickers:
            try:
                profiles[ticker] = self.get_company_profile(ticker)
            except Exception as e:
                logger.warning("Erro ao buscar %s: %s", ticker, e)
        return profiles

    def _extract_financials(self, info: dict) -> FinancialData:
        return FinancialData(
            revenue=_safe_get(info, "totalRevenue"),
            net_income=_safe_get(info, "netIncomeToCommon"),
            ebitda=_safe_get(info, "ebitda"),
            total_debt=_safe_get(info, "totalDebt"),
            total_cash=_safe_get(info, "totalCash"),
            total_assets=None,
            total_equity=None,
            free_cash_flow=_safe_get(info, "freeCashflow"),
            operating_margin=_safe_get(info, "operatingMargins"),
            profit_margin=_safe_get(info, "profitMargins"),
            roe=_safe_get(info, "returnOnEquity"),
            roa=_safe_get(info, "returnOnAssets"),
            current_ratio=_safe_get(info, "currentRatio"),
            debt_to_equity=_safe_get(info, "debtToEquity"),
            dividend_yield=_safe_get(info, "dividendYield"),
            payout_ratio=_safe_get(info, "payoutRatio"),
        )

    def _extract_valuation(self, info: dict) -> ValuationMetrics:
        return ValuationMetrics(
            pe_ratio=_safe_get(info, "trailingPE"),
            forward_pe=_safe_get(info, "forwardPE"),
            peg_ratio=_safe_get(info, "pegRatio"),
            pb_ratio=_safe_get(info, "priceToBook"),
            ps_ratio=_safe_get(info, "priceToSalesTrailing12Months"),
            ev_ebitda=_safe_get(info, "enterpriseToEbitda"),
            ev_revenue=_safe_get(info, "enterpriseToRevenue"),
            market_cap=_safe_get(info, "marketCap"),
            enterprise_value=_safe_get(info, "enterpriseValue"),
        )

    def _compute_technicals(self, stock: yf.Ticker) -> TechnicalIndicators:
        """Calcula indicadores tecnicos a partir do historico."""
        try:
            hist = stock.history(period="1y", interval="1d")
        except Exception:
            return TechnicalIndicators()

        if hist.empty or len(hist) < 20:
            return TechnicalIndicators()

        close = hist["Close"]
        volume = hist["Volume"]
        high = hist["High"]
        low = hist["Low"]

        indicators = TechnicalIndicators()

        # Medias moveis simples
        if len(close) >= 20:
            indicators.sma_20 = float(close.rolling(20).mean().iloc[-1])
        if len(close) >= 50:
            indicators.sma_50 = float(close.rolling(50).mean().iloc[-1])
        if len(close) >= 200:
            indicators.sma_200 = float(close.rolling(200).mean().iloc[-1])

        # Medias moveis exponenciais
        indicators.ema_12 = float(close.ewm(span=12).mean().iloc[-1])
        indicators.ema_26 = float(close.ewm(span=26).mean().iloc[-1])

        # RSI
        indicators.rsi_14 = self._compute_rsi(close, 14)

        # MACD
        macd_line = close.ewm(span=12).mean() - close.ewm(span=26).mean()
        signal_line = macd_line.ewm(span=9).mean()
        indicators.macd = float(macd_line.iloc[-1])
        indicators.macd_signal = float(signal_line.iloc[-1])
        indicators.macd_histogram = float((macd_line - signal_line).iloc[-1])

        # Bollinger Bands
        if len(close) >= 20:
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            indicators.bollinger_middle = float(sma20.iloc[-1])
            indicators.bollinger_upper = float(sma20.iloc[-1] + 2 * std20.iloc[-1])
            indicators.bollinger_lower = float(sma20.iloc[-1] - 2 * std20.iloc[-1])

        # ATR
        if len(close) >= 15:
            indicators.atr_14 = self._compute_atr(high, low, close, 14)

        # Volume medio
        if len(volume) >= 20:
            indicators.volume_avg_20 = float(volume.rolling(20).mean().iloc[-1])

        # Variacao de preco
        current = float(close.iloc[-1])
        if len(close) >= 2:
            indicators.price_change_1d = (current / float(close.iloc[-2]) - 1) * 100
        if len(close) >= 6:
            indicators.price_change_5d = (current / float(close.iloc[-6]) - 1) * 100
        if len(close) >= 22:
            indicators.price_change_1m = (current / float(close.iloc[-22]) - 1) * 100
        if len(close) >= 66:
            indicators.price_change_3m = (current / float(close.iloc[-66]) - 1) * 100
        if len(close) >= 126:
            indicators.price_change_6m = (current / float(close.iloc[-126]) - 1) * 100
        if len(close) >= 252:
            indicators.price_change_1y = (current / float(close.iloc[-252]) - 1) * 100

        # Volatilidade (desvio padrao dos retornos diarios anualizado)
        if len(close) >= 30:
            returns = close.pct_change().dropna().tail(30)
            indicators.volatility_30d = float(returns.std() * np.sqrt(252) * 100)

        # Beta
        info = stock.info
        indicators.beta = _safe_get(info, "beta")

        return indicators

    @staticmethod
    def _compute_rsi(series: pd.Series, period: int = 14) -> float | None:
        if len(series) < period + 1:
            return None
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = (-delta.clip(upper=0))
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        last_avg_loss = float(avg_loss.iloc[-1])
        if last_avg_loss == 0:
            return 100.0
        rs = float(avg_gain.iloc[-1]) / last_avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    @staticmethod
    def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return float(tr.rolling(period).mean().iloc[-1])
