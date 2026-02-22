"""Motor de analise fundamentalista."""

from __future__ import annotations

from .models import (
    AnalysisResult,
    CompanyProfile,
    Recommendation,
    RiskLevel,
)


class FundamentalAnalyzer:
    """Realiza analise fundamentalista de empresas."""

    # Pesos para o score geral
    WEIGHT_PROFITABILITY = 0.25
    WEIGHT_GROWTH = 0.15
    WEIGHT_HEALTH = 0.20
    WEIGHT_VALUATION = 0.25
    WEIGHT_DIVIDEND = 0.15

    def analyze(self, profile: CompanyProfile) -> AnalysisResult:
        """Executa analise fundamentalista completa."""
        profitability_score = self._score_profitability(profile)
        health_score = self._score_financial_health(profile)
        valuation_score = self._score_valuation(profile)
        dividend_score = self._score_dividends(profile)
        growth_score = self._score_growth(profile)

        fundamental_score = (
            profitability_score * self.WEIGHT_PROFITABILITY
            + growth_score * self.WEIGHT_GROWTH
            + health_score * self.WEIGHT_HEALTH
            + valuation_score * self.WEIGHT_VALUATION
            + dividend_score * self.WEIGHT_DIVIDEND
        )

        strengths, weaknesses = self._identify_strengths_weaknesses(profile)
        risk = self._assess_risk(profile, health_score)
        recommendation = self._make_recommendation(fundamental_score, valuation_score, risk)

        key_metrics = self._collect_key_metrics(profile)

        return AnalysisResult(
            ticker=profile.ticker,
            company_name=profile.name,
            fundamental_score=fundamental_score,
            valuation_score=valuation_score,
            risk_level=risk,
            recommendation=recommendation,
            strengths=strengths,
            weaknesses=weaknesses,
            key_metrics=key_metrics,
            summary=self._generate_summary(
                profile, fundamental_score, valuation_score, risk, recommendation
            ),
        )

    def _score_profitability(self, profile: CompanyProfile) -> float:
        """Pontua lucratividade (0-100)."""
        fin = profile.financials
        score = 50.0  # Base neutra

        if fin.profit_margin is not None:
            if fin.profit_margin > 0.20:
                score += 20
            elif fin.profit_margin > 0.10:
                score += 10
            elif fin.profit_margin > 0:
                score += 5
            else:
                score -= 15

        if fin.operating_margin is not None:
            if fin.operating_margin > 0.25:
                score += 15
            elif fin.operating_margin > 0.15:
                score += 10
            elif fin.operating_margin > 0:
                score += 5
            else:
                score -= 10

        if fin.roe is not None:
            if fin.roe > 0.20:
                score += 15
            elif fin.roe > 0.10:
                score += 10
            elif fin.roe > 0:
                score += 5
            else:
                score -= 10

        return max(0, min(100, score))

    def _score_financial_health(self, profile: CompanyProfile) -> float:
        """Pontua saude financeira (0-100)."""
        fin = profile.financials
        score = 50.0

        if fin.current_ratio is not None:
            if fin.current_ratio > 2.0:
                score += 15
            elif fin.current_ratio > 1.5:
                score += 10
            elif fin.current_ratio > 1.0:
                score += 5
            else:
                score -= 15

        if fin.debt_to_equity is not None:
            if fin.debt_to_equity < 30:
                score += 15
            elif fin.debt_to_equity < 80:
                score += 10
            elif fin.debt_to_equity < 150:
                score += 0
            else:
                score -= 15

        if fin.free_cash_flow is not None:
            if fin.free_cash_flow > 0:
                score += 10
            else:
                score -= 10

        return max(0, min(100, score))

    def _score_valuation(self, profile: CompanyProfile) -> float:
        """Pontua valuation (0-100). Scores altos = empresa barata."""
        val = profile.valuation
        score = 50.0

        if val.pe_ratio is not None:
            if val.pe_ratio < 0:
                score -= 20  # Prejuizo
            elif val.pe_ratio < 10:
                score += 20
            elif val.pe_ratio < 15:
                score += 15
            elif val.pe_ratio < 20:
                score += 5
            elif val.pe_ratio < 30:
                score -= 5
            else:
                score -= 15

        if val.peg_ratio is not None:
            if 0 < val.peg_ratio < 1.0:
                score += 15
            elif val.peg_ratio < 1.5:
                score += 10
            elif val.peg_ratio < 2.0:
                score += 5
            else:
                score -= 5

        if val.pb_ratio is not None:
            if val.pb_ratio < 1.0:
                score += 10
            elif val.pb_ratio < 3.0:
                score += 5
            elif val.pb_ratio > 10:
                score -= 10

        if val.ev_ebitda is not None:
            if val.ev_ebitda < 8:
                score += 10
            elif val.ev_ebitda < 12:
                score += 5
            elif val.ev_ebitda > 20:
                score -= 10

        # Upside ao preco alvo
        if profile.target_price and profile.current_price:
            upside = (profile.target_price / profile.current_price - 1) * 100
            if upside > 30:
                score += 10
            elif upside > 15:
                score += 5
            elif upside < -10:
                score -= 10

        return max(0, min(100, score))

    def _score_dividends(self, profile: CompanyProfile) -> float:
        """Pontua politica de dividendos (0-100)."""
        fin = profile.financials
        score = 50.0

        if fin.dividend_yield is not None:
            if fin.dividend_yield > 0.06:
                score += 15
            elif fin.dividend_yield > 0.03:
                score += 10
            elif fin.dividend_yield > 0.01:
                score += 5
            # Sem dividendo nao penaliza (pode ser growth)

        if fin.payout_ratio is not None:
            if 0.3 <= fin.payout_ratio <= 0.6:
                score += 10
            elif fin.payout_ratio > 0.9:
                score -= 10  # Payout insustentavel

        return max(0, min(100, score))

    def _score_growth(self, profile: CompanyProfile) -> float:
        """Pontua perspectiva de crescimento (0-100)."""
        val = profile.valuation
        fin = profile.financials
        score = 50.0

        if val.forward_pe and val.pe_ratio:
            if val.pe_ratio > 0 and val.forward_pe > 0:
                if val.forward_pe < val.pe_ratio:
                    score += 15  # Lucro crescendo
                else:
                    score -= 5

        if fin.revenue and fin.revenue > 0:
            score += 5

        if fin.free_cash_flow and fin.free_cash_flow > 0:
            score += 10

        return max(0, min(100, score))

    def _identify_strengths_weaknesses(
        self, profile: CompanyProfile
    ) -> tuple[list[str], list[str]]:
        """Identifica pontos fortes e fracos."""
        strengths = []
        weaknesses = []
        fin = profile.financials
        val = profile.valuation

        # Lucratividade
        if fin.profit_margin and fin.profit_margin > 0.15:
            strengths.append(f"Margem liquida alta: {fin.profit_margin:.1%}")
        elif fin.profit_margin and fin.profit_margin < 0:
            weaknesses.append("Empresa com prejuizo")

        if fin.roe and fin.roe > 0.15:
            strengths.append(f"ROE forte: {fin.roe:.1%}")
        elif fin.roe and fin.roe < 0:
            weaknesses.append(f"ROE negativo: {fin.roe:.1%}")

        # Saude financeira
        if fin.current_ratio and fin.current_ratio > 2.0:
            strengths.append(f"Liquidez solida: {fin.current_ratio:.2f}")
        elif fin.current_ratio and fin.current_ratio < 1.0:
            weaknesses.append(f"Liquidez preocupante: {fin.current_ratio:.2f}")

        if fin.debt_to_equity is not None:
            if fin.debt_to_equity < 50:
                strengths.append(f"Endividamento baixo: D/E {fin.debt_to_equity:.0f}%")
            elif fin.debt_to_equity > 150:
                weaknesses.append(f"Endividamento elevado: D/E {fin.debt_to_equity:.0f}%")

        if fin.free_cash_flow and fin.free_cash_flow > 0:
            strengths.append("Geracao de caixa livre positiva")
        elif fin.free_cash_flow and fin.free_cash_flow < 0:
            weaknesses.append("Queima de caixa")

        # Valuation
        if val.pe_ratio and 0 < val.pe_ratio < 15:
            strengths.append(f"P/L atrativo: {val.pe_ratio:.1f}x")
        elif val.pe_ratio and val.pe_ratio > 30:
            weaknesses.append(f"P/L esticado: {val.pe_ratio:.1f}x")

        # Dividendos
        if fin.dividend_yield and fin.dividend_yield > 0.04:
            strengths.append(f"Dividend Yield atrativo: {fin.dividend_yield:.1%}")

        # Upside
        if profile.target_price and profile.current_price:
            upside = (profile.target_price / profile.current_price - 1) * 100
            if upside > 20:
                strengths.append(f"Upside de {upside:.0f}% ao preco-alvo dos analistas")
            elif upside < -10:
                weaknesses.append(f"Downside de {abs(upside):.0f}% ao preco-alvo dos analistas")

        return strengths, weaknesses

    def _assess_risk(self, profile: CompanyProfile, health_score: float) -> RiskLevel:
        """Avalia nivel de risco."""
        risk_points = 0

        fin = profile.financials
        tech = profile.technicals

        if fin.debt_to_equity and fin.debt_to_equity > 150:
            risk_points += 2
        if fin.current_ratio and fin.current_ratio < 1.0:
            risk_points += 2
        if fin.profit_margin and fin.profit_margin < 0:
            risk_points += 2
        if tech.volatility_30d and tech.volatility_30d > 50:
            risk_points += 1
        if tech.beta and tech.beta > 1.5:
            risk_points += 1
        if health_score < 35:
            risk_points += 1

        if risk_points >= 5:
            return RiskLevel.VERY_HIGH
        elif risk_points >= 4:
            return RiskLevel.HIGH
        elif risk_points >= 2:
            return RiskLevel.MODERATE
        elif risk_points >= 1:
            return RiskLevel.LOW
        return RiskLevel.VERY_LOW

    def _make_recommendation(
        self, fundamental_score: float, valuation_score: float, risk: RiskLevel
    ) -> Recommendation:
        """Gera recomendacao baseada nos scores."""
        combined = (fundamental_score * 0.6 + valuation_score * 0.4)

        if risk in (RiskLevel.VERY_HIGH, RiskLevel.HIGH):
            combined -= 10

        if combined >= 75:
            return Recommendation.STRONG_BUY
        elif combined >= 62:
            return Recommendation.BUY
        elif combined >= 45:
            return Recommendation.HOLD
        elif combined >= 35:
            return Recommendation.SELL
        return Recommendation.STRONG_SELL

    def _collect_key_metrics(self, profile: CompanyProfile) -> dict:
        """Coleta metricas-chave para o relatorio."""
        metrics: dict = {}
        fin = profile.financials
        val = profile.valuation

        if profile.current_price:
            metrics["Preco Atual"] = f"{profile.currency} {profile.current_price:,.2f}"
        if profile.target_price:
            metrics["Preco-Alvo"] = f"{profile.currency} {profile.target_price:,.2f}"
        if val.market_cap:
            metrics["Market Cap"] = self._format_large_number(val.market_cap)
        if val.pe_ratio:
            metrics["P/L"] = f"{val.pe_ratio:.1f}x"
        if val.pb_ratio:
            metrics["P/VP"] = f"{val.pb_ratio:.1f}x"
        if val.ev_ebitda:
            metrics["EV/EBITDA"] = f"{val.ev_ebitda:.1f}x"
        if fin.roe:
            metrics["ROE"] = f"{fin.roe:.1%}"
        if fin.profit_margin:
            metrics["Margem Liquida"] = f"{fin.profit_margin:.1%}"
        if fin.dividend_yield:
            metrics["Dividend Yield"] = f"{fin.dividend_yield:.1%}"
        if fin.debt_to_equity is not None:
            metrics["D/E"] = f"{fin.debt_to_equity:.0f}%"

        return metrics

    @staticmethod
    def _format_large_number(value: float) -> str:
        if value >= 1e12:
            return f"${value / 1e12:.2f}T"
        elif value >= 1e9:
            return f"${value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"${value / 1e6:.2f}M"
        return f"${value:,.0f}"

    def _generate_summary(
        self,
        profile: CompanyProfile,
        fundamental_score: float,
        valuation_score: float,
        risk: RiskLevel,
        recommendation: Recommendation,
    ) -> str:
        """Gera resumo textual da analise."""
        parts = [
            f"{profile.name} ({profile.ticker}) - Setor: {profile.sector.value}",
            f"Score Fundamentalista: {fundamental_score:.0f}/100 | "
            f"Valuation: {valuation_score:.0f}/100",
            f"Risco: {risk.value} | Recomendacao: {recommendation.value}",
        ]
        if profile.current_price and profile.target_price:
            upside = (profile.target_price / profile.current_price - 1) * 100
            parts.append(
                f"Preco: {profile.currency} {profile.current_price:.2f} | "
                f"Alvo: {profile.currency} {profile.target_price:.2f} ({upside:+.1f}%)"
            )
        return " | ".join(parts)
