#!/usr/bin/env python3
"""
Investment Analysis Framework
Assistente inteligente de investimentos com IA (DeepSeek).

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
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print_error(
            "DEEPSEEK_API_KEY não configurada!\n"
            "  1. Copie .env.example para .env\n"
            "  2. Adicione sua chave: DEEPSEEK_API_KEY=sk-...\n"
            "  Ou exporte: export DEEPSEEK_API_KEY=sk-..."
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


def run_technical_analysis():
    """Análise técnica de uma ação (sem IA, apenas indicadores)."""
    ticker = input("Ticker para análise técnica: ").strip().upper()
    if not ticker:
        print_error("Ticker inválido.")
        return

    from financial_tools import get_technical_indicators

    print_streaming_start(f"Calculando indicadores técnicos de {ticker}...")

    result = get_technical_indicators(ticker)
    if "erro" in result:
        print_error(result["erro"])
        return

    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        console = Console()

        # Tendência geral
        tendencia = result["tendencia_geral"]
        cor = "green" if tendencia == "Alta" else "red" if tendencia == "Baixa" else "yellow"
        console.print(f"\n[bold {cor}]Tendência: {tendencia}[/bold {cor}]")
        console.print(f"Preço atual: {result['preco_atual']}\n")

        # Indicadores
        t = Table(title=f"Indicadores Técnicos - {ticker}", border_style="blue")
        t.add_column("Indicador", style="cyan")
        t.add_column("Valor", style="white")
        t.add_column("Interpretação", style="yellow")

        t.add_row("RSI (14)", str(result["rsi_14"]), result["rsi_interpretacao"])
        macd = result["macd"]
        t.add_row("MACD", str(macd["linha_macd"]), macd["interpretacao"])
        t.add_row("MACD Signal", str(macd["linha_sinal"]), "")
        t.add_row("MACD Histograma", str(macd["histograma"]), "")

        bb = result["bollinger_bands"]
        t.add_row("Bollinger Superior", str(bb["banda_superior"]), "")
        t.add_row("Bollinger Média", str(bb["banda_media"]), "")
        t.add_row("Bollinger Inferior", str(bb["banda_inferior"]), "")
        t.add_row("Posição nas Bandas", f"{bb['posicao_relativa']:.0%}", "")

        ma = result["medias_moveis"]
        t.add_row("SMA 20", str(ma["sma_20"]), "")
        t.add_row("SMA 50", str(ma["sma_50"]), "")
        t.add_row("SMA 200", str(ma["sma_200"]), "")

        sr = result["suporte_resistencia"]
        t.add_row("Resistência 2", str(sr["resistencia_2"]), "")
        t.add_row("Resistência 1", str(sr["resistencia_1"]), "")
        t.add_row("Pivô", str(sr["pivo"]), "")
        t.add_row("Suporte 1", str(sr["suporte_1"]), "")
        t.add_row("Suporte 2", str(sr["suporte_2"]), "")

        vol = result["volume"]
        t.add_row("Volume 5d/20d", str(vol["ratio_5d_vs_20d"]), vol["interpretacao"])

        console.print(t)

        # Sinais
        sinais = result["sinais_tecnicos"]
        sinais_text = "\n".join(f"  • {s}" for s in sinais)
        console.print(Panel(sinais_text, title="[bold yellow]Sinais Técnicos[/bold yellow]", border_style="yellow"))

    except ImportError:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))


def run_stock_screener():
    """Filtra ações por estratégia de investimento."""
    print()
    print_info("Selecione a estratégia de screening:\n")
    print("  [1] Value - ações baratas (baixo P/E e P/B)")
    print("  [2] Growth - alto crescimento de receita e lucros")
    print("  [3] Dividend - alto dividend yield sustentável")
    print("  [4] Momentum - tendência de alta confirmada")
    print("  [5] Quality - alto ROE e margens, baixa dívida")
    print("  [6] Undervalued - preço abaixo do valor justo")
    print()

    strategies = {"1": "value", "2": "growth", "3": "dividend", "4": "momentum", "5": "quality", "6": "undervalued"}
    choice = input("Escolha (1-6): ").strip()
    strategy = strategies.get(choice, "value")

    print("\nMercado:")
    print("  [1] EUA (S&P 500 + NASDAQ)")
    print("  [2] Brasil (IBOVESPA)")
    print("  [3] FIIs Brasileiros")
    markets = {"1": "us", "2": "br", "3": "fiis"}
    m_choice = input("Escolha (1-3): ").strip()
    market = markets.get(m_choice, "us")

    from stock_screener import screen_stocks

    print_streaming_start(f"Filtrando ações ({strategy}/{market})... pode levar alguns segundos")

    result = screen_stocks(strategy=strategy, market=market, limit=10)
    if "erro" in result:
        print_error(result["erro"])
        return

    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()

        console.print(f"\n[bold]Estratégia:[/bold] {strategy.upper()}")
        console.print(f"[bold]Critérios:[/bold] {result['criterios']}")
        console.print(f"[dim]Ações analisadas: {result['total_analisados']}[/dim]\n")

        resultados = result["resultados"]
        if not resultados:
            print_info("Nenhuma ação encontrada com os critérios selecionados.")
            return

        t = Table(title=f"Top {len(resultados)} - {strategy.upper()}", border_style="green")
        t.add_column("#", style="dim", width=3)
        t.add_column("Ticker", style="cyan bold")
        t.add_column("Nome", style="white", max_width=25)
        t.add_column("Preço", style="white", justify="right")

        # Colunas dinâmicas baseadas na estratégia
        first = resultados[0]
        score_key = [k for k in first if k.startswith("score_")][0] if any(k.startswith("score_") for k in first) else None
        extra_keys = [k for k in first if k not in ("ticker", "nome", "preco", score_key)]

        for key in extra_keys[:4]:
            label = key.replace("_pct", " %").replace("_", " ").title()
            t.add_column(label, style="yellow", justify="right")

        if score_key:
            t.add_column("Score", style="green bold", justify="right")

        for i, r in enumerate(resultados, 1):
            row = [str(i), r["ticker"], str(r.get("nome", ""))[:25], str(r.get("preco", "N/A"))]
            for key in extra_keys[:4]:
                row.append(str(r.get(key, "N/A")))
            if score_key:
                row.append(str(r.get(score_key, "N/A")))
            t.add_row(*row)

        console.print(t)

    except ImportError:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))


def run_portfolio_analysis():
    """Analisa uma carteira de investimentos."""
    _check_api_key()
    print()
    print_info("Análise de Portfólio - insira os tickers da sua carteira.\n")

    tickers_str = input("Tickers (separados por vírgula, ex: AAPL,MSFT,GOOGL): ").strip()
    if not tickers_str:
        print_error("Nenhum ticker informado.")
        return

    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
    if len(tickers) < 2:
        print_error("Informe pelo menos 2 tickers.")
        return

    weights_str = input(f"Pesos (separados por vírgula, ou Enter para pesos iguais): ").strip()
    weights = None
    if weights_str:
        try:
            weights = [float(w.strip()) for w in weights_str.split(",")]
        except ValueError:
            print_info("Pesos inválidos, usando pesos iguais.")

    print("\nDeseja análise com IA (mais detalhada) ou apenas dados?")
    print("  [1] Com IA (recomendado)")
    print("  [2] Apenas dados")
    ai_choice = input("Escolha (1-2): ").strip()

    if ai_choice == "2":
        # Análise sem IA
        from portfolio_analyzer import analyze_portfolio

        print_streaming_start("Analisando portfólio...")
        result = analyze_portfolio(tickers=tickers, weights=weights)
        if "erro" in result:
            print_error(result["erro"])
            return
        _display_portfolio_result(result)
    else:
        # Análise com IA
        print_streaming_start("Analisando portfólio com IA...")
        advisor = _get_advisor()

        weights_desc = ""
        if weights:
            pairs = [f"{t}: {w:.0%}" for t, w in zip(tickers, weights)]
            weights_desc = f"Pesos: {', '.join(pairs)}"
        else:
            weights_desc = "Pesos iguais"

        prompt = f"""Analise minha carteira de investimentos:

**Ativos:** {', '.join(tickers)}
**{weights_desc}**

Faça uma análise completa incluindo:
1. Análise individual de cada ativo (use os dados reais)
2. Análise do portfólio como um todo (correlação, diversificação, risco)
3. Pontos fortes e fracos da carteira
4. Sugestões de melhorias e rebalanceamento
5. Ativos que poderiam complementar a carteira

Use as ferramentas de análise de portfólio e dados individuais."""

        response = advisor.chat(prompt)
        print()
        print_response(response, "Análise de Portfólio")
        path = save_markdown_report(response, "Análise de Portfólio", "portfolio")
        print_success(f"Relatório salvo em: {path}")


def _display_portfolio_result(result: dict):
    """Exibe resultado da análise de portfólio."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        console = Console()

        port = result["portfolio"]
        console.print(f"\n[bold green]Retorno Total:[/bold green] {port['retorno_total_pct']}%")
        console.print(f"[bold]Retorno Anualizado:[/bold] {port['retorno_anualizado_pct']}%")
        console.print(f"[bold]Volatilidade:[/bold] {port['volatilidade_anualizada_pct']}%")
        console.print(f"[bold]Sharpe Ratio:[/bold] {port['sharpe_ratio']}")
        console.print(f"[bold red]Max Drawdown:[/bold red] {port['max_drawdown_pct']}%\n")

        # Ativos individuais
        t = Table(title="Ativos Individuais", border_style="blue")
        t.add_column("Ticker", style="cyan bold")
        t.add_column("Peso", justify="right")
        t.add_column("Retorno", justify="right")
        t.add_column("Volatilidade", justify="right")
        t.add_column("Sharpe", justify="right")
        t.add_column("Max DD", justify="right")

        for a in result["ativos_individuais"]:
            t.add_row(
                a["ticker"],
                f"{a['peso_pct']}%",
                f"{a['retorno_total_pct']}%",
                f"{a['volatilidade_anualizada_pct']}%",
                str(a["sharpe_ratio"]),
                f"{a['max_drawdown_pct']}%",
            )
        console.print(t)

        # Diversificação
        div = result["diversificacao"]
        console.print(f"\n[bold]Correlação média:[/bold] {div['correlacao_media']}")
        console.print(f"[bold]Diversificação:[/bold] {div['avaliacao']}")
        console.print(f"[bold]Concentração:[/bold] {div['avaliacao_concentracao']}\n")

        # Sugestões
        sugestoes = "\n".join(f"  • {s}" for s in result["sugestoes"])
        console.print(Panel(sugestoes, title="[bold yellow]Sugestões[/bold yellow]", border_style="yellow"))

    except ImportError:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))


def interactive_menu():
    """Menu principal interativo."""
    print_welcome()

    menu = {
        "1": "Análise Completa de Empresa (IA + dados reais)",
        "2": "Relatório do Mercado Atual",
        "3": "Estratégia de Investimento Personalizada",
        "4": "Chat com o Advisor (perguntas livres)",
        "5": "Stock Screener (filtrar ações por estratégia)",
        "6": "Análise Técnica (RSI, MACD, Bollinger)",
        "7": "Análise de Portfólio (carteira de ações)",
        "8": "Dados Rápidos de uma Ação (sem IA)",
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
            run_stock_screener()

        elif choice == "6":
            run_technical_analysis()

        elif choice == "7":
            run_portfolio_analysis()

        elif choice == "8":
            run_quick_analysis()

        else:
            print_error("Opção inválida.")


def main():
    parser = argparse.ArgumentParser(
        description="Investment Analysis Framework - Assistente inteligente de investimentos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py                          # menu interativo
  python main.py --analyze AAPL           # análise completa de Apple
  python main.py --analyze PETR4.SA       # análise de Petrobras
  python main.py --market                 # relatório de mercado
  python main.py --chat                   # chat livre com o advisor
  python main.py --screen value --market-filter br  # screener value BR
  python main.py --technical NVDA         # indicadores técnicos
        """,
    )

    parser.add_argument("--analyze", metavar="TICKER", help="Analisa uma empresa específica")
    parser.add_argument("--market", action="store_true", help="Gera relatório do mercado atual")
    parser.add_argument("--chat", action="store_true", help="Inicia chat livre com o advisor")
    parser.add_argument("--no-save", action="store_true", help="Não salva relatório em arquivo")
    parser.add_argument("--screen", metavar="STRATEGY", help="Stock screener: value, growth, dividend, momentum, quality, undervalued")
    parser.add_argument("--market-filter", metavar="MARKET", default="us", help="Mercado para screener: us, br, fiis (padrão: us)")
    parser.add_argument("--technical", metavar="TICKER", help="Análise técnica de uma ação")

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
    elif args.screen:
        print_welcome()
        from stock_screener import screen_stocks as _screen
        print_streaming_start(f"Filtrando ações ({args.screen}/{args.market_filter})...")
        result = _screen(strategy=args.screen, market=args.market_filter, limit=10)
        if "erro" in result:
            print_error(result["erro"])
        else:
            import json
            try:
                from rich.console import Console
                Console().print_json(json.dumps(result, ensure_ascii=False, default=str))
            except ImportError:
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    elif args.technical:
        print_welcome()
        from financial_tools import get_technical_indicators as _tech
        print_streaming_start(f"Indicadores técnicos de {args.technical.upper()}...")
        result = _tech(args.technical)
        if "erro" in result:
            print_error(result["erro"])
        else:
            import json
            try:
                from rich.console import Console
                Console().print_json(json.dumps(result, ensure_ascii=False, default=str))
            except ImportError:
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
