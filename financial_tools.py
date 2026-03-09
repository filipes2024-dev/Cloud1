"""
Ferramentas de dados financeiros usando yfinance.
Cada função retorna dados estruturados para análise via IA.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any

try:
    import yfinance as yf
    import pandas as pd
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


def _fetch_ticker_info(ticker: str, retries: int = 2) -> dict:
    """Busca info de um ticker com retry automático."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            info = yf.Ticker(ticker).info
            if info and info.get("regularMarketPrice") is not None:
                return info
            return {}
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1 * (attempt + 1))
    raise last_err or RuntimeError(f"Falha ao buscar {ticker}")


def _check_yfinance():
    if not YFINANCE_AVAILABLE:
        return {"erro": "yfinance não instalado. Execute: pip install yfinance pandas"}
    return None


def get_stock_overview(ticker: str) -> dict[str, Any]:
    """
    Retorna visão geral de uma ação: preço atual, variação, volume,
    market cap, P/E, dividendos, 52-week range.
    """
    err = _check_yfinance()
    if err:
        return err

    try:
        info = _fetch_ticker_info(ticker.upper())

        if not info:
            return {"erro": f"Ticker '{ticker}' não encontrado ou sem dados disponíveis."}

        current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
        variation = ((current_price - prev_close) / prev_close * 100) if prev_close else 0

        return {
            "ticker": ticker.upper(),
            "nome": info.get("longName", "N/A"),
            "setor": info.get("sector", "N/A"),
            "industria": info.get("industry", "N/A"),
            "pais": info.get("country", "N/A"),
            "bolsa": info.get("exchange", "N/A"),
            "moeda": info.get("currency", "N/A"),
            "preco_atual": round(current_price, 2),
            "variacao_pct": round(variation, 2),
            "volume": info.get("volume", 0),
            "volume_medio": info.get("averageVolume", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "dividend_yield": info.get("dividendYield"),
            "eps": info.get("trailingEps"),
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "media_50d": info.get("fiftyDayAverage"),
            "media_200d": info.get("twoHundredDayAverage"),
            "target_price": info.get("targetMeanPrice"),
            "recomendacao": info.get("recommendationKey", "N/A"),
            "num_analistas": info.get("numberOfAnalystOpinions"),
            "free_float": info.get("floatShares"),
            "acoes_em_circulacao": info.get("sharesOutstanding"),
        }
    except Exception as e:
        return {"erro": f"Erro ao buscar dados de {ticker}: {str(e)}"}


def get_financial_statements(ticker: str) -> dict[str, Any]:
    """
    Retorna demonstrações financeiras: receita, lucro, margens,
    fluxo de caixa e balanço patrimonial.
    """
    err = _check_yfinance()
    if err:
        return err

    try:
        stock = yf.Ticker(ticker.upper())

        result = {"ticker": ticker.upper()}

        # Demonstração de resultados
        try:
            income = stock.financials
            if income is not None and not income.empty:
                inc = income.iloc[:, 0]
                result["demonstracao_resultados"] = {
                    "receita_total": _safe_int(inc.get("Total Revenue")),
                    "receita_bruta": _safe_int(inc.get("Gross Profit")),
                    "ebit": _safe_int(inc.get("EBIT")),
                    "ebitda": _safe_int(inc.get("EBITDA")),
                    "lucro_liquido": _safe_int(inc.get("Net Income")),
                    "lucro_operacional": _safe_int(inc.get("Operating Income")),
                    "periodo": str(income.columns[0].date()) if not income.empty else "N/A",
                }
        except Exception:
            result["demonstracao_resultados"] = {"aviso": "Dados não disponíveis"}

        # Balanço patrimonial
        try:
            balance = stock.balance_sheet
            if balance is not None and not balance.empty:
                bal = balance.iloc[:, 0]
                result["balanco_patrimonial"] = {
                    "ativo_total": _safe_int(bal.get("Total Assets")),
                    "ativo_circulante": _safe_int(bal.get("Current Assets")),
                    "caixa": _safe_int(bal.get("Cash And Cash Equivalents")),
                    "passivo_total": _safe_int(bal.get("Total Liabilities Net Minority Interest")),
                    "divida_total": _safe_int(bal.get("Total Debt")),
                    "divida_liquida": _safe_int(bal.get("Net Debt")),
                    "patrimonio_liquido": _safe_int(bal.get("Stockholders Equity")),
                    "periodo": str(balance.columns[0].date()) if not balance.empty else "N/A",
                }
        except Exception:
            result["balanco_patrimonial"] = {"aviso": "Dados não disponíveis"}

        # Fluxo de caixa
        try:
            cashflow = stock.cashflow
            if cashflow is not None and not cashflow.empty:
                cf = cashflow.iloc[:, 0]
                result["fluxo_de_caixa"] = {
                    "operacional": _safe_int(cf.get("Operating Cash Flow")),
                    "investimentos": _safe_int(cf.get("Investing Cash Flow")),
                    "financiamentos": _safe_int(cf.get("Financing Cash Flow")),
                    "free_cash_flow": _safe_int(cf.get("Free Cash Flow")),
                    "capex": _safe_int(cf.get("Capital Expenditure")),
                    "periodo": str(cashflow.columns[0].date()) if not cashflow.empty else "N/A",
                }
        except Exception:
            result["fluxo_de_caixa"] = {"aviso": "Dados não disponíveis"}

        # Margens e crescimento (info)
        try:
            info = stock.info
            result["margens_e_retornos"] = {
                "margem_bruta": info.get("grossMargins"),
                "margem_operacional": info.get("operatingMargins"),
                "margem_lucro": info.get("profitMargins"),
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "crescimento_receita_yoy": info.get("revenueGrowth"),
                "crescimento_lucro_yoy": info.get("earningsGrowth"),
            }
        except Exception:
            result["margens_e_retornos"] = {"aviso": "Dados não disponíveis"}

        return result

    except Exception as e:
        return {"erro": f"Erro ao buscar demonstrações de {ticker}: {str(e)}"}


def get_price_history(ticker: str, period: str = "1y") -> dict[str, Any]:
    """
    Retorna histórico de preços e indicadores técnicos.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    err = _check_yfinance()
    if err:
        return err

    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)

        if hist.empty:
            return {"erro": f"Sem histórico para {ticker} no período {period}"}

        first = hist.iloc[0]
        last = hist.iloc[-1]
        perf = ((last["Close"] - first["Close"]) / first["Close"] * 100)

        high = hist["High"].max()
        low = hist["Low"].min()
        avg_vol = hist["Volume"].mean()

        # Últimos 10 dias
        recent = hist.tail(10)[["Close", "Volume"]].copy()
        recent.index = recent.index.strftime("%Y-%m-%d")
        recent_list = [
            {"data": d, "fechamento": round(row["Close"], 2), "volume": int(row["Volume"])}
            for d, row in recent.iterrows()
        ]

        return {
            "ticker": ticker.upper(),
            "periodo": period,
            "preco_inicio": round(float(first["Close"]), 2),
            "preco_atual": round(float(last["Close"]), 2),
            "performance_pct": round(float(perf), 2),
            "maximo_periodo": round(float(high), 2),
            "minimo_periodo": round(float(low), 2),
            "volume_medio_diario": int(avg_vol),
            "ultimos_10_dias": recent_list,
            "num_pregoes": len(hist),
        }

    except Exception as e:
        return {"erro": f"Erro ao buscar histórico de {ticker}: {str(e)}"}


def get_market_indices() -> dict[str, Any]:
    """
    Retorna cotações dos principais índices de mercado globais e brasileiros.
    """
    err = _check_yfinance()
    if err:
        return err

    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "IBOVESPA": "^BVSP",
        "IFIX (FIIs BR)": "IFIX.SA",
        "VIX (Volatilidade)": "^VIX",
        "DAX (Alemanha)": "^GDAXI",
        "Nikkei 225 (Japão)": "^N225",
        "Shanghai": "000001.SS",
        "Ouro": "GC=F",
        "Petróleo WTI": "CL=F",
        "Bitcoin/USD": "BTC-USD",
        "Dólar/Real": "BRL=X",
        "Euro/Dólar": "EURUSD=X",
    }

    result = {}
    for name, symbol in indices.items():
        try:
            t = yf.Ticker(symbol)
            info = t.info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
            change = ((price - prev) / prev * 100) if price and prev else None
            result[name] = {
                "simbolo": symbol,
                "valor": round(price, 2) if price else "N/A",
                "variacao_pct": round(change, 2) if change is not None else "N/A",
            }
        except Exception:
            result[name] = {"simbolo": symbol, "valor": "N/A", "variacao_pct": "N/A"}

    return {"indices_mercado": result, "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M")}


def get_sector_analysis(ticker: str) -> dict[str, Any]:
    """
    Compara a empresa com pares do mesmo setor (P/E, P/B, crescimento, margens).
    """
    err = _check_yfinance()
    if err:
        return err

    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")

        peers_tickers = _get_sector_peers(ticker.upper(), sector)

        peers_data = []
        for peer in peers_tickers:
            try:
                p = yf.Ticker(peer)
                pi = p.info
                if pi:
                    peers_data.append({
                        "ticker": peer,
                        "nome": pi.get("longName", "N/A"),
                        "market_cap": pi.get("marketCap"),
                        "pe_ratio": pi.get("trailingPE"),
                        "pb_ratio": pi.get("priceToBook"),
                        "margem_lucro": pi.get("profitMargins"),
                        "crescimento_receita": pi.get("revenueGrowth"),
                        "dividend_yield": pi.get("dividendYield"),
                    })
            except Exception:
                continue

        empresa_atual = {
            "ticker": ticker.upper(),
            "nome": info.get("longName", "N/A"),
            "setor": sector,
            "industria": industry,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "margem_lucro": info.get("profitMargins"),
            "crescimento_receita": info.get("revenueGrowth"),
            "dividend_yield": info.get("dividendYield"),
        }

        return {
            "empresa": empresa_atual,
            "setor": sector,
            "industria": industry,
            "pares_setor": peers_data,
            "nota": "Comparação para avaliação relativa de valuation",
        }

    except Exception as e:
        return {"erro": f"Erro na análise setorial de {ticker}: {str(e)}"}


def get_dividends_history(ticker: str) -> dict[str, Any]:
    """
    Retorna histórico de dividendos e splits nos últimos 3 anos.
    """
    err = _check_yfinance()
    if err:
        return err

    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        divs = stock.dividends
        splits = stock.splits

        three_years_ago = datetime.now() - timedelta(days=3 * 365)

        divs_list = []
        if divs is not None and not divs.empty:
            recent_divs = divs[divs.index >= pd.Timestamp(three_years_ago, tz="UTC")]
            divs_list = [
                {"data": str(d.date()), "valor": round(float(v), 4)}
                for d, v in recent_divs.items()
            ]

        splits_list = []
        if splits is not None and not splits.empty:
            recent_splits = splits[splits.index >= pd.Timestamp(three_years_ago, tz="UTC")]
            splits_list = [
                {"data": str(d.date()), "proporcao": f"{int(v)}:1"}
                for d, v in recent_splits.items()
            ]

        total_div = sum(d["valor"] for d in divs_list)

        return {
            "ticker": ticker.upper(),
            "nome": info.get("longName", "N/A"),
            "dividend_yield_atual": info.get("dividendYield"),
            "dividendo_anual": info.get("dividendRate"),
            "payout_ratio": info.get("payoutRatio"),
            "dividendos_ultimos_3_anos": divs_list,
            "total_dividendos_3_anos": round(total_div, 4),
            "splits_ultimos_3_anos": splits_list,
        }

    except Exception as e:
        return {"erro": f"Erro ao buscar dividendos de {ticker}: {str(e)}"}


def calculate_investment_metrics(ticker: str, preco_alvo: float = None) -> dict[str, Any]:
    """
    Calcula métricas de investimento: DCF simplificado, Graham Number,
    margem de segurança e score de qualidade.
    """
    err = _check_yfinance()
    if err:
        return err

    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        preco = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        eps = info.get("trailingEps", 0) or 0
        bvps = info.get("bookValue", 0) or 0
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        roe = info.get("returnOnEquity", 0) or 0
        div_yield = info.get("dividendYield", 0) or 0
        growth = info.get("earningsGrowth", 0) or 0
        beta = info.get("beta", 1) or 1
        target = info.get("targetMeanPrice") or preco_alvo

        # Graham Number
        graham_number = None
        if eps > 0 and bvps > 0:
            import math
            graham_number = round(math.sqrt(22.5 * eps * bvps), 2)

        # Margem de segurança em relação ao target dos analistas
        margem_seguranca = None
        if target and preco:
            margem_seguranca = round((target - preco) / preco * 100, 2)

        # Score de qualidade (0-100)
        score = _calculate_quality_score(info)

        # Indicador de risco
        risco = "Alto" if (beta or 1) > 1.5 else "Moderado" if (beta or 1) > 0.8 else "Baixo"

        return {
            "ticker": ticker.upper(),
            "nome": info.get("longName", "N/A"),
            "preco_atual": round(preco, 2) if preco else "N/A",
            "graham_number": graham_number,
            "target_analistas": round(target, 2) if target else "N/A",
            "margem_seguranca_pct": margem_seguranca,
            "pe_ratio": pe,
            "pb_ratio": pb,
            "roe_pct": round(roe * 100, 2) if roe else "N/A",
            "dividend_yield_pct": round(div_yield * 100, 2) if div_yield else "N/A",
            "crescimento_lucros_pct": round(growth * 100, 2) if growth else "N/A",
            "beta": beta,
            "nivel_risco": risco,
            "score_qualidade": score,
            "interpretacao_score": _interpret_score(score),
        }

    except Exception as e:
        return {"erro": f"Erro ao calcular métricas de {ticker}: {str(e)}"}


# --- Helpers internos ---

def _safe_int(val) -> int | None:
    try:
        if val is None or (isinstance(val, float) and str(val) == "nan"):
            return None
        return int(val)
    except Exception:
        return None


def _get_sector_peers(ticker: str, sector: str) -> list[str]:
    """Retorna peers pré-definidos por setor para comparação."""
    peers_map = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN"],
        "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS", "C"],
        "Healthcare": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "TMO"],
        "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX"],
        "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST", "CL"],
        "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC"],
        "Industrials": ["GE", "HON", "UPS", "CAT", "DE", "MMM"],
        "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "DLR", "O"],
        "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC"],
        "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T"],
        "Basic Materials": ["LIN", "APD", "ECL", "DD", "NEM", "FCX"],
    }
    all_peers = peers_map.get(sector, ["SPY", "QQQ"])
    return [p for p in all_peers if p != ticker][:5]


def _calculate_quality_score(info: dict) -> int:
    """Score de qualidade de 0 a 100 baseado em múltiplos indicadores."""
    score = 50  # base

    roe = info.get("returnOnEquity", 0) or 0
    if roe > 0.20:
        score += 10
    elif roe > 0.10:
        score += 5
    elif roe < 0:
        score -= 10

    profit_margin = info.get("profitMargins", 0) or 0
    if profit_margin > 0.20:
        score += 10
    elif profit_margin > 0.10:
        score += 5
    elif profit_margin < 0:
        score -= 10

    debt_to_equity = info.get("debtToEquity", 100) or 100
    if debt_to_equity < 30:
        score += 10
    elif debt_to_equity < 100:
        score += 5
    elif debt_to_equity > 200:
        score -= 10

    growth = info.get("revenueGrowth", 0) or 0
    if growth > 0.20:
        score += 10
    elif growth > 0.05:
        score += 5
    elif growth < -0.05:
        score -= 10

    rec = info.get("recommendationKey", "")
    if rec in ("strong_buy", "buy"):
        score += 5
    elif rec in ("sell", "strong_sell"):
        score -= 5

    return max(0, min(100, score))


def _interpret_score(score: int) -> str:
    if score >= 80:
        return "Excelente - empresa de alta qualidade"
    elif score >= 65:
        return "Bom - empresa sólida com fundamentos positivos"
    elif score >= 50:
        return "Regular - empresa com pontos positivos e negativos"
    elif score >= 35:
        return "Fraco - empresa com fundamentos preocupantes"
    else:
        return "Muito fraco - alto risco, análise aprofundada necessária"


def get_technical_indicators(ticker: str, period: str = "6mo") -> dict[str, Any]:
    """
    Calcula indicadores técnicos: RSI, MACD, Bollinger Bands,
    médias móveis, suportes/resistências e sinais de trading.
    """
    err = _check_yfinance()
    if err:
        return err

    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)

        if hist.empty or len(hist) < 26:
            return {"erro": f"Dados insuficientes para análise técnica de {ticker}"}

        close = hist["Close"]

        # --- RSI (14 períodos) ---
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean()
        avg_loss = loss.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_current = round(float(rsi.iloc[-1]), 2) if not rsi.empty else None

        # --- MACD (12, 26, 9) ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line

        macd_current = round(float(macd_line.iloc[-1]), 4)
        signal_current = round(float(signal_line.iloc[-1]), 4)
        macd_hist_current = round(float(macd_hist.iloc[-1]), 4)

        # --- Bollinger Bands (20, 2) ---
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)

        bb_upper_val = round(float(bb_upper.iloc[-1]), 2)
        bb_lower_val = round(float(bb_lower.iloc[-1]), 2)
        bb_middle_val = round(float(sma20.iloc[-1]), 2)
        preco_atual = round(float(close.iloc[-1]), 2)

        # Posição relativa nas bandas (0 = banda inferior, 1 = banda superior)
        bb_width = bb_upper_val - bb_lower_val
        bb_position = round((preco_atual - bb_lower_val) / bb_width, 2) if bb_width > 0 else 0.5

        # --- Médias Móveis ---
        sma50 = close.rolling(window=50).mean() if len(close) >= 50 else None
        sma200 = close.rolling(window=200).mean() if len(close) >= 200 else None

        sma50_val = round(float(sma50.iloc[-1]), 2) if sma50 is not None and not sma50.empty else None
        sma200_val = round(float(sma200.iloc[-1]), 2) if sma200 is not None and not sma200.empty else None

        # --- Suportes e Resistências (pivô simples) ---
        high = float(hist["High"].iloc[-1])
        low = float(hist["Low"].iloc[-1])
        pivot = round((high + low + preco_atual) / 3, 2)
        suporte_1 = round(2 * pivot - high, 2)
        resistencia_1 = round(2 * pivot - low, 2)
        suporte_2 = round(pivot - (high - low), 2)
        resistencia_2 = round(pivot + (high - low), 2)

        # --- Volume médio recente vs histórico ---
        vol_5d = float(hist["Volume"].tail(5).mean())
        vol_20d = float(hist["Volume"].tail(20).mean())
        volume_ratio = round(vol_5d / vol_20d, 2) if vol_20d > 0 else 1.0

        # --- Sinais ---
        sinais = []

        if rsi_current is not None:
            if rsi_current > 70:
                sinais.append("RSI sobrecomprado (>70) - possível correção")
            elif rsi_current < 30:
                sinais.append("RSI sobrevendido (<30) - possível oportunidade de compra")

        if macd_hist_current > 0 and float(macd_hist.iloc[-2]) <= 0:
            sinais.append("MACD cruzou acima do sinal - sinal de compra")
        elif macd_hist_current < 0 and float(macd_hist.iloc[-2]) >= 0:
            sinais.append("MACD cruzou abaixo do sinal - sinal de venda")

        if bb_position > 0.95:
            sinais.append("Preço próximo à banda superior de Bollinger - possível sobrecompra")
        elif bb_position < 0.05:
            sinais.append("Preço próximo à banda inferior de Bollinger - possível sobrevenda")

        if sma50_val and sma200_val:
            if sma50_val > sma200_val and preco_atual > sma50_val:
                sinais.append("Golden Cross ativo (SMA50 > SMA200) - tendência de alta")
            elif sma50_val < sma200_val and preco_atual < sma50_val:
                sinais.append("Death Cross ativo (SMA50 < SMA200) - tendência de baixa")

        if volume_ratio > 1.5:
            sinais.append(f"Volume recente {volume_ratio}x acima da média - atenção ao movimento")

        # --- Tendência geral ---
        if preco_atual > bb_middle_val and (rsi_current or 50) > 50 and macd_hist_current > 0:
            tendencia = "Alta"
        elif preco_atual < bb_middle_val and (rsi_current or 50) < 50 and macd_hist_current < 0:
            tendencia = "Baixa"
        else:
            tendencia = "Lateral/Indefinida"

        return {
            "ticker": ticker.upper(),
            "periodo_analise": period,
            "preco_atual": preco_atual,
            "tendencia_geral": tendencia,
            "rsi_14": rsi_current,
            "rsi_interpretacao": (
                "Sobrecomprado" if (rsi_current or 50) > 70
                else "Sobrevendido" if (rsi_current or 50) < 30
                else "Neutro"
            ),
            "macd": {
                "linha_macd": macd_current,
                "linha_sinal": signal_current,
                "histograma": macd_hist_current,
                "interpretacao": "Bullish" if macd_hist_current > 0 else "Bearish",
            },
            "bollinger_bands": {
                "banda_superior": bb_upper_val,
                "banda_media": bb_middle_val,
                "banda_inferior": bb_lower_val,
                "posicao_relativa": bb_position,
            },
            "medias_moveis": {
                "sma_20": bb_middle_val,
                "sma_50": sma50_val,
                "sma_200": sma200_val,
            },
            "suporte_resistencia": {
                "pivo": pivot,
                "suporte_1": suporte_1,
                "suporte_2": suporte_2,
                "resistencia_1": resistencia_1,
                "resistencia_2": resistencia_2,
            },
            "volume": {
                "ratio_5d_vs_20d": volume_ratio,
                "interpretacao": "Volume elevado" if volume_ratio > 1.5 else "Volume normal" if volume_ratio > 0.7 else "Volume baixo",
            },
            "sinais_tecnicos": sinais if sinais else ["Sem sinais relevantes no momento"],
        }

    except Exception as e:
        return {"erro": f"Erro na análise técnica de {ticker}: {str(e)}"}
