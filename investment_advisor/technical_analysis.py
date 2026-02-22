"""Motor de analise tecnica."""

from __future__ import annotations

from .models import CompanyProfile, TechnicalIndicators


class TechnicalAnalyzer:
    """Realiza analise tecnica de ativos."""

    def analyze(self, profile: CompanyProfile) -> dict:
        """Executa analise tecnica completa e retorna score + sinais."""
        tech = profile.technicals
        signals: list[dict] = []

        trend_score = self._analyze_trend(tech, signals)
        momentum_score = self._analyze_momentum(tech, signals)
        volatility_score = self._analyze_volatility(tech, signals)
        volume_score = self._analyze_volume(tech, signals)

        overall_score = (
            trend_score * 0.35
            + momentum_score * 0.30
            + volatility_score * 0.20
            + volume_score * 0.15
        )

        verdict = self._overall_verdict(overall_score)

        return {
            "score": round(overall_score, 1),
            "trend_score": round(trend_score, 1),
            "momentum_score": round(momentum_score, 1),
            "volatility_score": round(volatility_score, 1),
            "volume_score": round(volume_score, 1),
            "verdict": verdict,
            "signals": signals,
        }

    def _analyze_trend(self, tech: TechnicalIndicators, signals: list[dict]) -> float:
        """Analisa tendencia (medias moveis)."""
        score = 50.0
        price = None

        # Tenta inferir preco atual das medias
        for val in [tech.sma_20, tech.ema_12, tech.sma_50]:
            if val is not None:
                price = val
                break

        if tech.sma_20 and tech.sma_50:
            if tech.sma_20 > tech.sma_50:
                score += 10
                signals.append({
                    "tipo": "ALTA",
                    "indicador": "SMA",
                    "descricao": "Media de 20 dias acima da de 50 - tendencia de alta",
                })
            else:
                score -= 10
                signals.append({
                    "tipo": "BAIXA",
                    "indicador": "SMA",
                    "descricao": "Media de 20 dias abaixo da de 50 - tendencia de baixa",
                })

        if tech.sma_50 and tech.sma_200:
            if tech.sma_50 > tech.sma_200:
                score += 15
                signals.append({
                    "tipo": "ALTA",
                    "indicador": "Golden Cross",
                    "descricao": "SMA 50 acima da SMA 200 - sinal bullish de longo prazo",
                })
            else:
                score -= 15
                signals.append({
                    "tipo": "BAIXA",
                    "indicador": "Death Cross",
                    "descricao": "SMA 50 abaixo da SMA 200 - sinal bearish de longo prazo",
                })

        # Preco vs medias
        if price and tech.sma_200:
            pct_above_200 = (price / tech.sma_200 - 1) * 100
            if pct_above_200 > 10:
                score += 10
            elif pct_above_200 < -10:
                score -= 10

        # Variacao recente
        if tech.price_change_1m is not None:
            if tech.price_change_1m > 5:
                score += 5
            elif tech.price_change_1m < -5:
                score -= 5

        return max(0, min(100, score))

    def _analyze_momentum(self, tech: TechnicalIndicators, signals: list[dict]) -> float:
        """Analisa momentum (RSI, MACD)."""
        score = 50.0

        # RSI
        if tech.rsi_14 is not None:
            if tech.rsi_14 > 70:
                score -= 15
                signals.append({
                    "tipo": "ATENCAO",
                    "indicador": "RSI",
                    "descricao": f"RSI em {tech.rsi_14:.0f} - sobrecomprado, possivel correcao",
                })
            elif tech.rsi_14 < 30:
                score += 15
                signals.append({
                    "tipo": "OPORTUNIDADE",
                    "indicador": "RSI",
                    "descricao": f"RSI em {tech.rsi_14:.0f} - sobrevendido, possivel recuperacao",
                })
            elif 40 <= tech.rsi_14 <= 60:
                score += 5
                signals.append({
                    "tipo": "NEUTRO",
                    "indicador": "RSI",
                    "descricao": f"RSI em {tech.rsi_14:.0f} - zona neutra",
                })

        # MACD
        if tech.macd is not None and tech.macd_signal is not None:
            if tech.macd > tech.macd_signal:
                score += 10
                signals.append({
                    "tipo": "ALTA",
                    "indicador": "MACD",
                    "descricao": "MACD acima da linha de sinal - momentum positivo",
                })
            else:
                score -= 10
                signals.append({
                    "tipo": "BAIXA",
                    "indicador": "MACD",
                    "descricao": "MACD abaixo da linha de sinal - momentum negativo",
                })

        if tech.macd_histogram is not None:
            if tech.macd_histogram > 0:
                score += 5
            else:
                score -= 5

        # Bollinger Bands
        if tech.bollinger_upper and tech.bollinger_lower and tech.sma_20:
            price = tech.sma_20  # Aproximacao
            bb_width = tech.bollinger_upper - tech.bollinger_lower
            if bb_width > 0:
                bb_pct = (price - tech.bollinger_lower) / bb_width
                if bb_pct > 0.95:
                    signals.append({
                        "tipo": "ATENCAO",
                        "indicador": "Bollinger",
                        "descricao": "Preco proximo da banda superior - resistencia",
                    })
                elif bb_pct < 0.05:
                    signals.append({
                        "tipo": "OPORTUNIDADE",
                        "indicador": "Bollinger",
                        "descricao": "Preco proximo da banda inferior - suporte",
                    })

        return max(0, min(100, score))

    def _analyze_volatility(self, tech: TechnicalIndicators, signals: list[dict]) -> float:
        """Analisa volatilidade."""
        score = 60.0  # Volatilidade moderada e ideal

        if tech.volatility_30d is not None:
            if tech.volatility_30d > 60:
                score -= 20
                signals.append({
                    "tipo": "RISCO",
                    "indicador": "Volatilidade",
                    "descricao": f"Volatilidade muito alta: {tech.volatility_30d:.0f}% anualizada",
                })
            elif tech.volatility_30d > 40:
                score -= 10
            elif tech.volatility_30d < 15:
                score += 10
                signals.append({
                    "tipo": "ESTAVEL",
                    "indicador": "Volatilidade",
                    "descricao": f"Volatilidade baixa: {tech.volatility_30d:.0f}% anualizada",
                })

        if tech.beta is not None:
            if tech.beta > 1.5:
                score -= 10
            elif tech.beta < 0.8:
                score += 10

        if tech.atr_14 is not None and tech.sma_20 is not None and tech.sma_20 > 0:
            atr_pct = (tech.atr_14 / tech.sma_20) * 100
            if atr_pct > 5:
                score -= 10
            elif atr_pct < 1.5:
                score += 5

        return max(0, min(100, score))

    def _analyze_volume(self, tech: TechnicalIndicators, signals: list[dict]) -> float:
        """Analisa volume."""
        score = 50.0

        if tech.volume_avg_20 is not None:
            if tech.volume_avg_20 > 1_000_000:
                score += 15
                signals.append({
                    "tipo": "POSITIVO",
                    "indicador": "Volume",
                    "descricao": f"Volume medio alto: {tech.volume_avg_20:,.0f} acoes/dia",
                })
            elif tech.volume_avg_20 > 100_000:
                score += 5
            else:
                score -= 10
                signals.append({
                    "tipo": "ATENCAO",
                    "indicador": "Volume",
                    "descricao": "Baixa liquidez - volume medio inferior a 100k/dia",
                })

        return max(0, min(100, score))

    @staticmethod
    def _overall_verdict(score: float) -> str:
        if score >= 70:
            return "Forte tendencia de alta - sinais tecnicos favoraveis"
        elif score >= 55:
            return "Tendencia moderadamente positiva"
        elif score >= 45:
            return "Sinais mistos - mercado lateralizado"
        elif score >= 35:
            return "Tendencia moderadamente negativa"
        return "Forte tendencia de baixa - sinais tecnicos desfavoraveis"

    def format_report(self, profile: CompanyProfile, analysis: dict) -> str:
        """Formata o relatorio de analise tecnica em texto."""
        lines = [
            f"=== Analise Tecnica: {profile.name} ({profile.ticker}) ===",
            f"Score Geral: {analysis['score']}/100",
            f"Veredicto: {analysis['verdict']}",
            "",
            "Scores por Categoria:",
            f"  Tendencia:    {analysis['trend_score']}/100",
            f"  Momentum:     {analysis['momentum_score']}/100",
            f"  Volatilidade: {analysis['volatility_score']}/100",
            f"  Volume:       {analysis['volume_score']}/100",
            "",
            "Sinais Identificados:",
        ]
        for signal in analysis["signals"]:
            lines.append(f"  [{signal['tipo']}] {signal['indicador']}: {signal['descricao']}")

        tech = profile.technicals
        lines.append("")
        lines.append("Indicadores:")
        if tech.rsi_14 is not None:
            lines.append(f"  RSI(14): {tech.rsi_14:.1f}")
        if tech.macd is not None:
            lines.append(f"  MACD: {tech.macd:.4f}")
        if tech.sma_50 is not None:
            lines.append(f"  SMA(50): {tech.sma_50:.2f}")
        if tech.sma_200 is not None:
            lines.append(f"  SMA(200): {tech.sma_200:.2f}")
        if tech.volatility_30d is not None:
            lines.append(f"  Volatilidade 30d: {tech.volatility_30d:.1f}%")
        if tech.beta is not None:
            lines.append(f"  Beta: {tech.beta:.2f}")

        return "\n".join(lines)
