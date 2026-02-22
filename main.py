#!/usr/bin/env python3
"""
Investment Analysis Framework
Assistente inteligente de investimentos com IA (Claude Opus 4.6).

Uso:
    python main.py                    # modo interativo
    python main.py --analyze AAPL     # análise direta de uma ação
    python main.py --market           # relatório de mercado
    python main.py --chat             # chat livre com o advisor
"""

import argparse
import os
import sys
from pathlib import Path

# Carrega .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from report_generator import (
    print_welcome,
    print_menu,
    print_response,
    print_streaming_start,
    print_success,
    print_error,
    print_info,
    save_markdown_report,
)


def _check_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print_error(
            "ANTHROPIC_API_KEY não configurada!\n"
            "  1. Copie .env.example para .env\n"
            "  2. Adicione sua chave: ANTHROPIC_API_KEY=sk-ant-...\n"
            "  Ou exporte: export ANTHROPIC_API_KEY=sk-ant-..."
        )
        sys.exit(1)
    return key


def _get_advisor():
    from advisor import InvestmentAdvisor
    return InvestmentAdvisor()


def _streaming_printer():
    """Retorna callback para exibir texto em streaming."""
    try:
        from rich.console import Console
        console = Console()
        printed = {"chars": 0}

        def on_text(text: str):
            console.print(text, end="", markup=False, highlight=False)
            printed["chars"] += len(text)

        return on_text
    except ImportError:
        def on_text(text: str):
            print(text, end="", flush=True)
        return on_text


def run_company_analysis(ticker: str, save: bool = True):
    """Executa análise completa de uma empresa."""
    _check_api_key()
    print_streaming_start(f"Analisando {ticker.upper()}... (pode levar alguns segundos)")

    advisor = _get_advisor()
    response = advisor.analyze_company(ticker)

    print()
    if save:
        path = save_markdown_report(
            response,
            title=f"Análise de Investimento: {ticker.upper()}",
            ticker=ticker,
        )
        print_success(f"Relatório salvo em: {path}")

    return response


def run_market_report(save: bool = True):
    """Gera relatório do mercado atual."""
    _check_api_key()
    print_streaming_start("Gerando relatório de mercado...")

    advisor = _get_advisor()
    response = advisor.generate_market_report()

    print()
    if save:
        path = save_markdown_report(
            response,
            title="Relatório de Mercado",
            ticker="mercado",
        )
        print_success(f"Relatório salvo em: {path}")

    return response


def run_investment_strategy():
    """Coleta parâmetros e gera estratégia personalizada."""
    _check_api_key()
    print()
    print_info("Vamos criar sua estratégia de investimento personalizada.\n")

    print("Perfil do investidor:")
    print("  [1] Conservador - preservar capital, baixo risco")
    print("  [2] Moderado - crescimento equilibrado, risco médio")
    print("  [3] Agressivo - maximizar retorno, alto risco")
    print("  [4] Personalizado - descreva seu perfil")
    print()

    choice = input("Escolha (1-4): ").strip()
    profiles = {
        "1": "Conservador - prefiro preservar capital, aceito baixa rentabilidade por segurança",
        "2": "Moderado - busco crescimento equilibrado com risco controlado",
        "3": "Agressivo - aceito alta volatilidade em busca de retornos elevados",
    }
    if choice in profiles:
        profile = profiles[choice]
    else:
        profile = input("Descreva seu perfil: ").strip()
        if not profile:
            profile = "Moderado"

    amount_str = input("\nValor disponível para investir (R$): ").strip().replace(",", "").replace(".", "")
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 10000.0
        print_info("Valor inválido, usando R$ 10.000,00 como exemplo.")

    print("\nHorizonte de investimento:")
    print("  [1] Curto prazo (até 1 ano)")
    print("  [2] Médio prazo (1 a 5 anos)")
    print("  [3] Longo prazo (acima de 5 anos)")
    horizons = {
        "1": "Curto prazo (até 1 ano)",
        "2": "Médio prazo (1 a 5 anos)",
        "3": "Longo prazo (acima de 5 anos)",
    }
    h_choice = input("Escolha (1-3): ").strip()
    horizon = horizons.get(h_choice, "Médio prazo (1 a 5 anos)")

    print_streaming_start("Criando estratégia personalizada...")
    advisor = _get_advisor()
    response = advisor.investment_strategy(profile, amount, horizon)

    print()
    path = save_markdown_report(
        response,
        title="Estratégia de Investimento Personalizada",
        ticker="estrategia",
    )
    print_success(f"Estratégia salva em: {path}")
    return response


def run_chat_mode():
    """Modo de chat livre com o advisor."""
    _check_api_key()

    try:
        from rich.console import Console
        from rich.markdown import Markdown
        from rich.panel import Panel
        console = Console()

        def display_response(text: str):
            md = Markdown(text)
            console.print(Panel(md, border_style="cyan", title="[bold cyan]Advisor[/bold cyan]"))
    except ImportError:
        def display_response(text: str):
            print("\n" + "-" * 50)
            print(text)
            print("-" * 50)

    print_info(
        "\nModo de chat ativo. Digite 'sair' para encerrar, 'reset' para nova conversa, "
        "'salvar' para salvar o último relatório.\n"
    )

    advisor = _get_advisor()
    last_response = ""

    while True:
        try:
            user_input = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAté mais!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("sair", "exit", "quit", "q"):
            print_info("Encerrando chat. Até mais!")
            break
        elif cmd == "reset":
            advisor.reset_conversation()
            print_success("Conversa reiniciada.")
            continue
        elif cmd == "salvar" and last_response:
            path = save_markdown_report(last_response, "Chat - Investment Advisor")
            print_success(f"Salvo em: {path}")
            continue
        elif cmd == "ajuda":
            print_info(
                "Comandos: sair | reset | salvar\n"
                "Exemplos de perguntas:\n"
                "  - Analise AAPL para mim\n"
                "  - Quais são as melhores ações de dividendos agora?\n"
                "  - Como está o mercado hoje?\n"
                "  - O que é P/E ratio e como interpretar?\n"
                "  - Compare VALE3.SA com seus concorrentes\n"
                "  - Estratégia para investir R$ 50mil com perfil moderado"
            )
            continue

        print_streaming_start("Pensando...")
        try:
            response = advisor.chat(user_input)
            last_response = response
            print()
            display_response(response)
        except Exception as e:
            print_error(str(e))


def run_quick_analysis():
    """Análise rápida com dados brutos (sem IA, apenas dados)."""
    _check_api_key()
    ticker = input("Ticker para análise rápida: ").strip().upper()
    if not ticker:
        print_error("Ticker inválido.")
        return

    from financial_tools import (
        get_stock_overview,
        calculate_investment_metrics,
        get_price_history,
    )
    from report_generator import print_stock_summary

    print_streaming_start(f"Buscando dados de {ticker}...")

    overview = get_stock_overview(ticker)
    if "erro" in overview:
        print_error(overview["erro"])
        return

    print_stock_summary(overview)

    metrics = calculate_investment_metrics(ticker)
    history = get_price_history(ticker, "6mo")

    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()

        m_table = Table(title="Métricas de Investimento", border_style="yellow")
        m_table.add_column("Métrica", style="cyan")
        m_table.add_column("Valor", style="white")

        m_table.add_row("Graham Number", str(metrics.get("graham_number", "N/A")))
        m_table.add_row("Target Analistas", str(metrics.get("target_analistas", "N/A")))
        m_table.add_row("Margem de Segurança", f"{metrics.get('margem_seguranca_pct', 'N/A')}%")
        m_table.add_row("Score Qualidade", f"{metrics.get('score_qualidade', 'N/A')}/100")
        m_table.add_row("Nível de Risco", str(metrics.get("nivel_risco", "N/A")))
        m_table.add_row("ROE", f"{metrics.get('roe_pct', 'N/A')}%")
        m_table.add_row("Performance 6m", f"{history.get('performance_pct', 'N/A')}%")
        console.print(m_table)
        console.print(f"\n[dim]{metrics.get('interpretacao_score', '')}[/dim]\n")
    except ImportError:
        print(f"\nScore: {metrics.get('score_qualidade', 'N/A')}/100")
        print(f"Risco: {metrics.get('nivel_risco', 'N/A')}")
        print(f"Graham Number: {metrics.get('graham_number', 'N/A')}")


def interactive_menu():
    """Menu principal interativo."""
    print_welcome()

    menu = {
        "1": "Análise Completa de Empresa (com relatório IA)",
        "2": "Relatório do Mercado Atual",
        "3": "Estratégia de Investimento Personalizada",
        "4": "Chat com o Advisor (perguntas livres)",
        "5": "Dados Rápidos de uma Ação (sem IA)",
        "0": "Sair",
    }

    while True:
        print()
        print_menu(menu)
        print()

        try:
            choice = input("Escolha uma opção: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté mais!")
            break

        if choice == "0":
            print_info("Encerrando. Até mais!")
            break

        elif choice == "1":
            ticker = input("\nTicker da empresa (ex: AAPL, PETR4.SA, VALE3.SA): ").strip()
            if ticker:
                response = run_company_analysis(ticker)
                print_response(response, f"Análise: {ticker.upper()}")
            else:
                print_error("Ticker não informado.")

        elif choice == "2":
            response = run_market_report()
            print_response(response, "Relatório de Mercado")

        elif choice == "3":
            response = run_investment_strategy()
            print_response(response, "Estratégia de Investimento")

        elif choice == "4":
            run_chat_mode()

        elif choice == "5":
            run_quick_analysis()

        else:
            print_error("Opção inválida.")


def main():
    parser = argparse.ArgumentParser(
        description="Investment Analysis Framework - Assistente inteligente de investimentos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py                    # menu interativo
  python main.py --analyze AAPL     # análise completa de Apple
  python main.py --analyze PETR4.SA # análise de Petrobras
  python main.py --market           # relatório de mercado
  python main.py --chat             # chat livre com o advisor
        """,
    )

    parser.add_argument("--analyze", metavar="TICKER", help="Analisa uma empresa específica")
    parser.add_argument("--market", action="store_true", help="Gera relatório do mercado atual")
    parser.add_argument("--chat", action="store_true", help="Inicia chat livre com o advisor")
    parser.add_argument("--no-save", action="store_true", help="Não salva relatório em arquivo")

    args = parser.parse_args()

    if args.analyze:
        print_welcome()
        response = run_company_analysis(args.analyze, save=not args.no_save)
        print_response(response, f"Análise: {args.analyze.upper()}")
    elif args.market:
        print_welcome()
        response = run_market_report(save=not args.no_save)
        print_response(response, "Relatório de Mercado")
    elif args.chat:
        print_welcome()
        run_chat_mode()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
