"""
Portfolio Analyzer — analisa uma carteira de ações.
Calcula retorno, risco, correlação, diversificação e sugestões de rebalanceamento.
"""

import math
from datetime import datetime
from typing import Any

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def analyze_portfolio(
    tickers: list[str],
    weights: list[float] | None = None,
    period: str = "1y",
) -> dict[str, Any]:
    """
    Analisa uma carteira de investimentos.

    tickers: lista de tickers (ex: ["AAPL", "MSFT", "VALE3.SA"])
    weights: pesos de cada ativo (devem somar 1.0). Se None, assume equal-weight.
    period: período de análise (1mo, 3mo, 6mo, 1y, 2y, 5y)
    """
    if not AVAILABLE:
        return {"erro": "yfinance/pandas/numpy não instalados."}

    if not tickers or len(tickers) < 2:
        return {"erro": "Informe pelo menos 2 tickers para análise de portfólio."}

    n = len(tickers)
    tickers = [t.upper() for t in tickers]

    if weights is None:
        weights = [1.0 / n] * n
    elif len(weights) != n:
        return {"erro": f"Número de pesos ({len(weights)}) diferente do número de tickers ({n})."}
    else:
        total_w = sum(weights)
        weights = [w / total_w for w in weights]

    # Baixar dados
    try:
        data = yf.download(tickers, period=period, auto_adjust=True, progress=False)
    except Exception as e:
        return {"erro": f"Erro ao baixar dados: {str(e)}"}

    if data.empty:
        return {"erro": "Nenhum dado retornado para os tickers informados."}

    # Extrair preços de fechamento
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"]
    else:
        close = data[["Close"]].copy()
        close.columns = tickers

    # Remover colunas sem dados
    valid_tickers = []
    valid_weights = []
    for i, t in enumerate(tickers):
        if t in close.columns and close[t].notna().sum() > 10:
            valid_tickers.append(t)
            valid_weights.append(weights[i])

    if len(valid_tickers) < 2:
        return {"erro": "Dados insuficientes para pelo menos 2 ativos."}

    # Renormalizar pesos
    total_w = sum(valid_weights)
    valid_weights = [w / total_w for w in valid_weights]

    close = close[valid_tickers].dropna()
    returns = close.pct_change().dropna()

    # --- Métricas individuais ---
    individual = []
    for i, ticker in enumerate(valid_tickers):
        ret_series = returns[ticker]
        total_ret = float((close[ticker].iloc[-1] / close[ticker].iloc[0] - 1) * 100)
        annual_ret = float(ret_series.mean() * 252 * 100)
        annual_vol = float(ret_series.std() * math.sqrt(252) * 100)
        sharpe = (annual_ret / annual_vol) if annual_vol > 0 else 0

        # Max drawdown
        cumulative = (1 + ret_series).cumprod()
        running_max = cumulative.cummax()
        drawdown = ((cumulative - running_max) / running_max) * 100
        max_dd = float(drawdown.min())

        individual.append({
            "ticker": ticker,
            "peso_pct": round(valid_weights[i] * 100, 2),
            "retorno_total_pct": round(total_ret, 2),
            "retorno_anualizado_pct": round(annual_ret, 2),
            "volatilidade_anualizada_pct": round(annual_vol, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd, 2),
        })

    # --- Correlação ---
    corr_matrix = returns.corr()
    correlacoes = {}
    for i, t1 in enumerate(valid_tickers):
        for j, t2 in enumerate(valid_tickers):
            if i < j:
                correlacoes[f"{t1} x {t2}"] = round(float(corr_matrix.loc[t1, t2]), 3)

    # --- Métricas do portfólio ---
    w = np.array(valid_weights)
    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values

    port_return = float(np.dot(w, mean_returns) * 252 * 100)
    port_vol = float(math.sqrt(np.dot(w.T, np.dot(cov_matrix * 252, w))) * 100)
    port_sharpe = (port_return / port_vol) if port_vol > 0 else 0

    # Retorno total do portfólio
    port_daily = (returns * w).sum(axis=1)
    port_cumulative = (1 + port_daily).cumprod()
    port_total_ret = float((port_cumulative.iloc[-1] - 1) * 100)

    # Max drawdown do portfólio
    port_running_max = port_cumulative.cummax()
    port_drawdown = ((port_cumulative - port_running_max) / port_running_max) * 100
    port_max_dd = float(port_drawdown.min())

    # --- Diversificação ---
    avg_corr = sum(correlacoes.values()) / len(correlacoes) if correlacoes else 0
    if avg_corr < 0.3:
        diversificacao = "Excelente - baixa correlação entre ativos"
    elif avg_corr < 0.5:
        diversificacao = "Boa - correlação moderada"
    elif avg_corr < 0.7:
        diversificacao = "Regular - ativos correlacionados"
    else:
        diversificacao = "Fraca - ativos muito correlacionados, pouca diversificação"

    # --- Concentração (Herfindahl) ---
    hhi = sum(wi ** 2 for wi in valid_weights)
    if hhi < 0.15:
        concentracao = "Bem diversificado"
    elif hhi < 0.25:
        concentracao = "Concentração moderada"
    else:
        concentracao = "Altamente concentrado"

    # --- Sugestões ---
    sugestoes = []
    if avg_corr > 0.7:
        sugestoes.append("Considere adicionar ativos de setores/mercados diferentes para reduzir correlação.")
    if hhi > 0.25:
        sugestoes.append("Portfólio muito concentrado. Redistribua os pesos para reduzir risco.")
    if port_vol > 25:
        sugestoes.append("Volatilidade alta. Considere incluir ativos de renda fixa ou defensivos.")
    if port_sharpe < 0.5:
        sugestoes.append("Sharpe ratio baixo. Avalie se o retorno compensa o risco assumido.")

    worst = min(individual, key=lambda x: x["sharpe_ratio"])
    if worst["sharpe_ratio"] < 0:
        sugestoes.append(f"{worst['ticker']} tem Sharpe negativo — avalie se faz sentido manter.")

    if not sugestoes:
        sugestoes.append("Portfólio parece equilibrado. Continue monitorando periodicamente.")

    return {
        "periodo_analise": period,
        "num_ativos": len(valid_tickers),
        "portfolio": {
            "retorno_total_pct": round(port_total_ret, 2),
            "retorno_anualizado_pct": round(port_return, 2),
            "volatilidade_anualizada_pct": round(port_vol, 2),
            "sharpe_ratio": round(port_sharpe, 2),
            "max_drawdown_pct": round(port_max_dd, 2),
        },
        "diversificacao": {
            "correlacao_media": round(avg_corr, 3),
            "avaliacao": diversificacao,
            "indice_concentracao_hhi": round(hhi, 4),
            "avaliacao_concentracao": concentracao,
        },
        "ativos_individuais": individual,
        "correlacoes": correlacoes,
        "sugestoes": sugestoes,
    }
