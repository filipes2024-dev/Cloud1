"""Ponto de entrada principal do Investment AI Advisor."""

from __future__ import annotations

import argparse
import json
import sys

from .ai_advisor import AIAdvisor
from .cli import InvestmentCLI
from .fundamental_analysis import FundamentalAnalyzer
from .market_data import MarketDataProvider
from .technical_analysis import TechnicalAnalyzer


def quick_analyze(ticker: str) -> None:
    """Analise rapida de um ticker via linha de comando."""
    market_data = MarketDataProvider()
    fundamental = FundamentalAnalyzer()
    technical = TechnicalAnalyzer()

    try:
        profile = market_data.get_company_profile(ticker)
    except Exception as e:
        print(f"Erro ao buscar dados de {ticker}: {e}", file=sys.stderr)
        sys.exit(1)

    fund_result = fundamental.analyze(profile)
    tech_result = technical.analyze(profile)

    fund_result.technical_score = tech_result["score"]
    fund_result.overall_score = (
        fund_result.fundamental_score * 0.5
        + tech_result["score"] * 0.3
        + fund_result.valuation_score * 0.2
    )

    result = {
        "analise_fundamentalista": fund_result.to_report_dict(),
        "analise_tecnica": {
            "score": tech_result["score"],
            "veredicto": tech_result["verdict"],
            "sinais": tech_result["signals"],
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def ask_ai(question: str) -> None:
    """Faz uma pergunta direta ao assessor IA."""
    advisor = AIAdvisor()
    try:
        response = advisor.chat(question)
        print(response)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Funcao principal."""
    parser = argparse.ArgumentParser(
        description="Investment AI Advisor - Assessor de Investimentos com IA",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Comando: chat (padrao - interface interativa)
    subparsers.add_parser("chat", help="Inicia interface interativa (padrao)")

    # Comando: analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analise rapida de um ticker")
    analyze_parser.add_argument("ticker", help="Ticker da acao (ex: AAPL, PETR4.SA)")

    # Comando: ask
    ask_parser = subparsers.add_parser("ask", help="Faz uma pergunta ao assessor IA")
    ask_parser.add_argument("question", nargs="+", help="Pergunta para o assessor")

    args = parser.parse_args()

    if args.command == "analyze":
        quick_analyze(args.ticker)
    elif args.command == "ask":
        ask_ai(" ".join(args.question))
    else:
        cli = InvestmentCLI()
        cli.run()


if __name__ == "__main__":
    main()
