"""
Stock Screener — filtra ações por estratégia de investimento.
Estratégias pré-definidas: Value, Growth, Dividend, Momentum e Custom.
"""

import sys
import time
from typing import Any

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


# Universos de ações pré-definidos por mercado
UNIVERSO_BR = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "WEGE3.SA",
    "ABEV3.SA", "RENT3.SA", "BBAS3.SA", "B3SA3.SA", "SUZB3.SA",
    "GGBR4.SA", "CSNA3.SA", "RADL3.SA", "JBSS3.SA", "LREN3.SA",
    "VIVT3.SA", "CMIG4.SA", "ELET3.SA", "CPLE6.SA", "TAEE11.SA",
    "BBSE3.SA", "ENGI11.SA", "ENBR3.SA", "FLRY3.SA", "TOTS3.SA",
    "PRIO3.SA", "MGLU3.SA", "HAPV3.SA", "RAIL3.SA", "KLBN11.SA",
]

UNIVERSO_US = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    "BRK-B", "JPM", "JNJ", "V", "UNH", "HD", "PG", "MA",
    "DIS", "NFLX", "ADBE", "CRM", "PYPL", "INTC", "AMD",
    "KO", "PEP", "WMT", "COST", "MCD", "NKE", "T", "VZ",
    "XOM", "CVX", "PFE", "MRK", "ABBV", "LLY", "TMO",
    "BA", "GE", "CAT", "DE", "MMM",
]

UNIVERSO_FIIS = [
    "HGLG11.SA", "KNRI11.SA", "MXRF11.SA", "XPLG11.SA", "XPML11.SA",
    "VISC11.SA", "HGBS11.SA", "BTLG11.SA", "VILG11.SA", "IRDM11.SA",
    "RECR11.SA", "CPTS11.SA", "KNCR11.SA", "HGRE11.SA", "RBRR11.SA",
]


def _check():
    if not YFINANCE_AVAILABLE:
        return {"erro": "yfinance não instalado. Execute: pip install yfinance"}
    return None


def _fetch_info(ticker: str, retries: int = 2) -> dict | None:
    """Busca info de um ticker com retry, retorna None em caso de erro."""
    for attempt in range(retries + 1):
        try:
            info = yf.Ticker(ticker).info
            if info and info.get("regularMarketPrice") is not None:
                return info
            print(f"  [screener] {ticker}: sem dados de preço", file=sys.stderr)
            return None
        except Exception as e:
            if attempt < retries:
                time.sleep(1 * (attempt + 1))
            else:
                print(f"  [screener] {ticker}: erro após {retries + 1} tentativas - {e}", file=sys.stderr)
    return None


def screen_stocks(
    strategy: str = "value",
    market: str = "us",
    custom_tickers: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Filtra ações de acordo com a estratégia escolhida.

    strategy: value | growth | dividend | momentum | quality | undervalued
    market: us | br | fiis | custom
    custom_tickers: lista de tickers quando market='custom'
    limit: número máximo de resultados
    """
    err = _check()
    if err:
        return err

    # Selecionar universo
    if custom_tickers:
        universe = custom_tickers
    elif market.lower() == "br":
        universe = UNIVERSO_BR
    elif market.lower() == "fiis":
        universe = UNIVERSO_FIIS
    elif market.lower() == "us":
        universe = UNIVERSO_US
    else:
        universe = UNIVERSO_US

    strategy = strategy.lower()
    screeners = {
        "value": _screen_value,
        "growth": _screen_growth,
        "dividend": _screen_dividend,
        "momentum": _screen_momentum,
        "quality": _screen_quality,
        "undervalued": _screen_undervalued,
    }

    screen_fn = screeners.get(strategy)
    if not screen_fn:
        return {
            "erro": f"Estratégia '{strategy}' não encontrada. "
            f"Opções: {', '.join(screeners.keys())}"
        }

    # Coletar dados
    stocks_data = []
    failed_tickers = []
    for ticker in universe:
        info = _fetch_info(ticker)
        if info:
            stocks_data.append(info)
        else:
            failed_tickers.append(ticker)

    if not stocks_data:
        return {
            "erro": f"Nenhum dado obtido para o universo selecionado. "
            f"{len(failed_tickers)} tickers falharam: {', '.join(failed_tickers[:10])}. "
            "Possíveis causas: sem conexão com internet, yfinance bloqueado ou tickers inválidos."
        }

    # Filtrar e rankear
    results = screen_fn(stocks_data)
    results = results[:limit]

    resultado = {
        "estrategia": strategy,
        "mercado": market,
        "total_analisados": len(stocks_data),
        "resultados": results,
        "criterios": _get_criteria_description(strategy),
    }
    if failed_tickers:
        resultado["tickers_sem_dados"] = len(failed_tickers)
    return resultado


def _screen_value(stocks: list[dict]) -> list[dict]:
    """Value investing: baixo P/E, baixo P/B, margem positiva."""
    scored = []
    for s in stocks:
        pe = s.get("trailingPE")
        pb = s.get("priceToBook")
        margin = s.get("profitMargins", 0) or 0

        if pe is None or pb is None or pe <= 0 or pb <= 0:
            continue
        if margin <= 0:
            continue

        # Score: menor P/E e P/B = melhor
        score = 100 - min(pe, 50) - min(pb, 10) * 3 + margin * 100
        scored.append({
            "ticker": s.get("symbol", "N/A"),
            "nome": s.get("longName", "N/A"),
            "preco": s.get("currentPrice") or s.get("regularMarketPrice"),
            "pe_ratio": round(pe, 2),
            "pb_ratio": round(pb, 2),
            "margem_lucro": round(margin * 100, 2),
            "dividend_yield": round((s.get("dividendYield", 0) or 0) * 100, 2),
            "score_value": round(score, 2),
        })

    scored.sort(key=lambda x: x["score_value"], reverse=True)
    return scored


def _screen_growth(stocks: list[dict]) -> list[dict]:
    """Growth investing: alto crescimento de receita e lucros."""
    scored = []
    for s in stocks:
        rev_growth = s.get("revenueGrowth", 0) or 0
        earn_growth = s.get("earningsGrowth", 0) or 0

        if rev_growth <= 0 and earn_growth <= 0:
            continue

        score = rev_growth * 50 + earn_growth * 50
        scored.append({
            "ticker": s.get("symbol", "N/A"),
            "nome": s.get("longName", "N/A"),
            "preco": s.get("currentPrice") or s.get("regularMarketPrice"),
            "crescimento_receita_pct": round(rev_growth * 100, 2),
            "crescimento_lucro_pct": round(earn_growth * 100, 2),
            "pe_forward": round(s.get("forwardPE", 0) or 0, 2),
            "margem_operacional": round((s.get("operatingMargins", 0) or 0) * 100, 2),
            "score_growth": round(score * 100, 2),
        })

    scored.sort(key=lambda x: x["score_growth"], reverse=True)
    return scored


def _screen_dividend(stocks: list[dict]) -> list[dict]:
    """Dividend investing: alto yield e payout sustentável."""
    scored = []
    for s in stocks:
        div_yield = s.get("dividendYield", 0) or 0
        payout = s.get("payoutRatio", 0) or 0

        if div_yield <= 0.01:
            continue

        # Payout entre 30-70% é ideal; penalizar muito alto ou muito baixo
        payout_score = 10 if 0.3 <= payout <= 0.7 else 5 if payout < 0.9 else 0
        score = div_yield * 1000 + payout_score

        scored.append({
            "ticker": s.get("symbol", "N/A"),
            "nome": s.get("longName", "N/A"),
            "preco": s.get("currentPrice") or s.get("regularMarketPrice"),
            "dividend_yield_pct": round(div_yield * 100, 2),
            "payout_ratio_pct": round(payout * 100, 2),
            "pe_ratio": round((s.get("trailingPE") or 0), 2),
            "margem_lucro": round((s.get("profitMargins", 0) or 0) * 100, 2),
            "score_dividend": round(score, 2),
        })

    scored.sort(key=lambda x: x["score_dividend"], reverse=True)
    return scored


def _screen_momentum(stocks: list[dict]) -> list[dict]:
    """Momentum: preço acima das médias, performance recente forte."""
    scored = []
    for s in stocks:
        price = s.get("currentPrice") or s.get("regularMarketPrice", 0)
        sma50 = s.get("fiftyDayAverage", 0) or 0
        sma200 = s.get("twoHundredDayAverage", 0) or 0
        high52 = s.get("fiftyTwoWeekHigh", 0) or 0
        low52 = s.get("fiftyTwoWeekLow", 0) or 0

        if not price or not sma50 or not sma200:
            continue

        # Percentual acima das médias
        above_50 = ((price - sma50) / sma50 * 100) if sma50 else 0
        above_200 = ((price - sma200) / sma200 * 100) if sma200 else 0
        from_high = ((price - high52) / high52 * 100) if high52 else 0
        from_low = ((price - low52) / low52 * 100) if low52 else 0

        # Filtrar: preço acima de ambas as médias
        if price < sma50 or price < sma200:
            continue

        score = above_50 + above_200 * 0.5 + from_low * 0.3

        scored.append({
            "ticker": s.get("symbol", "N/A"),
            "nome": s.get("longName", "N/A"),
            "preco": round(price, 2),
            "vs_sma50_pct": round(above_50, 2),
            "vs_sma200_pct": round(above_200, 2),
            "vs_52w_high_pct": round(from_high, 2),
            "vs_52w_low_pct": round(from_low, 2),
            "score_momentum": round(score, 2),
        })

    scored.sort(key=lambda x: x["score_momentum"], reverse=True)
    return scored


def _screen_quality(stocks: list[dict]) -> list[dict]:
    """Quality: ROE alto, margens altas, baixo endividamento."""
    scored = []
    for s in stocks:
        roe = s.get("returnOnEquity", 0) or 0
        margin = s.get("profitMargins", 0) or 0
        dte = s.get("debtToEquity", 200) or 200

        if roe <= 0 or margin <= 0:
            continue

        # Score: alto ROE + alta margem + baixa dívida
        debt_score = max(0, 20 - dte / 10)
        score = roe * 100 + margin * 100 + debt_score

        scored.append({
            "ticker": s.get("symbol", "N/A"),
            "nome": s.get("longName", "N/A"),
            "preco": s.get("currentPrice") or s.get("regularMarketPrice"),
            "roe_pct": round(roe * 100, 2),
            "margem_lucro_pct": round(margin * 100, 2),
            "divida_patrimonio": round(dte, 2),
            "margem_operacional_pct": round((s.get("operatingMargins", 0) or 0) * 100, 2),
            "score_quality": round(score, 2),
        })

    scored.sort(key=lambda x: x["score_quality"], reverse=True)
    return scored


def _screen_undervalued(stocks: list[dict]) -> list[dict]:
    """Undervalued: preço abaixo do target dos analistas e/ou Graham Number."""
    import math
    scored = []
    for s in stocks:
        price = s.get("currentPrice") or s.get("regularMarketPrice", 0)
        target = s.get("targetMeanPrice")
        eps = s.get("trailingEps", 0) or 0
        bvps = s.get("bookValue", 0) or 0

        if not price:
            continue

        # Margem vs target
        margin_target = ((target - price) / price * 100) if target else 0

        # Graham Number
        graham = math.sqrt(22.5 * eps * bvps) if eps > 0 and bvps > 0 else None
        margin_graham = ((graham - price) / price * 100) if graham else 0

        combined_margin = margin_target * 0.6 + margin_graham * 0.4

        if combined_margin <= 0:
            continue

        scored.append({
            "ticker": s.get("symbol", "N/A"),
            "nome": s.get("longName", "N/A"),
            "preco": round(price, 2),
            "target_analistas": round(target, 2) if target else "N/A",
            "margem_vs_target_pct": round(margin_target, 2),
            "graham_number": round(graham, 2) if graham else "N/A",
            "margem_vs_graham_pct": round(margin_graham, 2),
            "recomendacao": s.get("recommendationKey", "N/A"),
            "score_undervalued": round(combined_margin, 2),
        })

    scored.sort(key=lambda x: x["score_undervalued"], reverse=True)
    return scored


def _get_criteria_description(strategy: str) -> str:
    descriptions = {
        "value": "Baixo P/E, baixo P/B, margens positivas. Empresas baratas em relação aos fundamentos.",
        "growth": "Alto crescimento de receita e lucros. Empresas em expansão acelerada.",
        "dividend": "Alto dividend yield com payout sustentável (30-70%). Renda passiva.",
        "momentum": "Preço acima das médias móveis (SMA50 e SMA200). Tendência de alta confirmada.",
        "quality": "Alto ROE, altas margens e baixo endividamento. Empresas de alta qualidade.",
        "undervalued": "Preço abaixo do target dos analistas e/ou Graham Number. Possível oportunidade de compra.",
    }
    return descriptions.get(strategy, "Estratégia personalizada.")
