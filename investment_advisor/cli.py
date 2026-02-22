"""Interface CLI interativa para o assessor de investimentos."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from .ai_advisor import AIAdvisor
from .fundamental_analysis import FundamentalAnalyzer
from .market_data import MarketDataProvider
from .portfolio_manager import PortfolioManager
from .technical_analysis import TechnicalAnalyzer

custom_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "danger": "red bold",
    "header": "bold magenta",
})

console = Console(theme=custom_theme)

BANNER = r"""
 ___                     _                        _        _    ___
|_ _|_ __ __   _____  __| |_ _ __ ___   ___ _ __ | |_     / \  |_ _|
 | || '_ \\ \ / / _ \/ _` | '_ ` _ \ / _ \ '_ \| __|   / _ \  | |
 | || | | |\ V /  __/ (_| | | | | | |  __/ | | | |_   / ___ \ | |
|___|_| |_| \_/ \___|\__,_|_| |_| |_|\___|_| |_|\__| /_/   \_\___|

             Assessor de Investimentos com IA
"""

HELP_TEXT = """
**Comandos disponiveis:**

| Comando | Descricao |
|---------|-----------|
| `/analisar <TICKER>` | Analisa uma empresa (ex: `/analisar AAPL`) |
| `/comparar <T1> <T2> ...` | Compara empresas (ex: `/comparar AAPL MSFT GOOGL`) |
| `/tecnica <TICKER>` | Analise tecnica detalhada |
| `/portfolio criar <nome>` | Cria nova carteira |
| `/portfolio ver <nome>` | Mostra carteira |
| `/portfolio add <nome> <ticker> <qtd> <preco>` | Adiciona posicao |
| `/portfolio rm <nome> <ticker> [qtd]` | Remove posicao |
| `/portfolio listar` | Lista todas as carteiras |
| `/screen <T1> <T2> ...` | Screening de acoes por score |
| `/limpar` | Limpa historico da conversa |
| `/ajuda` | Mostra esta ajuda |
| `/sair` | Encerra o programa |

**Ou simplesmente faca uma pergunta sobre investimentos!**
Exemplos:
- "Qual a melhor estrategia para investir em dividendos?"
- "Compare VALE3.SA com PETR4.SA"
- "Quais sao os riscos de investir em cripto?"
- "Monte uma carteira diversificada com R$50.000"
"""


class InvestmentCLI:
    """Interface de linha de comando interativa."""

    def __init__(self):
        self.advisor = AIAdvisor()
        self.market_data = MarketDataProvider()
        self.fundamental = FundamentalAnalyzer()
        self.technical = TechnicalAnalyzer()
        self.portfolio_mgr = PortfolioManager()

    def run(self) -> None:
        """Loop principal da CLI."""
        console.print(BANNER, style="header")
        console.print(
            "Bem-vindo ao seu assessor de investimentos pessoal com IA!",
            style="info",
        )
        console.print("Digite /ajuda para ver os comandos disponiveis.\n", style="info")

        while True:
            try:
                user_input = console.input("[bold cyan]Voce>[/] ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\nAte logo! Bons investimentos!", style="info")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                self._handle_command(user_input)
            else:
                self._handle_chat(user_input)

    def _handle_command(self, command: str) -> None:
        """Processa comandos especiais."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/sair":
            console.print("Ate logo! Bons investimentos!", style="info")
            sys.exit(0)

        elif cmd == "/ajuda":
            console.print(Markdown(HELP_TEXT))

        elif cmd == "/limpar":
            self.advisor.reset_conversation()
            console.print("Historico de conversa limpo.", style="success")

        elif cmd == "/analisar":
            if len(parts) < 2:
                console.print("Uso: /analisar <TICKER>", style="warning")
                return
            self._cmd_analyze(parts[1])

        elif cmd == "/comparar":
            if len(parts) < 3:
                console.print("Uso: /comparar <TICKER1> <TICKER2> ...", style="warning")
                return
            self._cmd_compare(parts[1:])

        elif cmd == "/tecnica":
            if len(parts) < 2:
                console.print("Uso: /tecnica <TICKER>", style="warning")
                return
            self._cmd_technical(parts[1])

        elif cmd == "/portfolio":
            self._cmd_portfolio(parts[1:])

        elif cmd == "/screen":
            if len(parts) < 2:
                console.print("Uso: /screen <TICKER1> <TICKER2> ...", style="warning")
                return
            self._cmd_screen(parts[1:])

        else:
            console.print(f"Comando desconhecido: {cmd}. Digite /ajuda.", style="warning")

    def _handle_chat(self, message: str) -> None:
        """Envia mensagem para o assessor IA."""
        with console.status("Analisando...", spinner="dots"):
            try:
                response = self.advisor.chat(message)
            except Exception as e:
                console.print(f"Erro ao comunicar com IA: {e}", style="danger")
                return

        console.print()
        console.print(Panel(Markdown(response), title="Assessor IA", border_style="cyan"))
        console.print()

    def _cmd_analyze(self, ticker: str) -> None:
        """Analise completa de uma empresa."""
        with console.status(f"Analisando {ticker.upper()}...", spinner="dots"):
            try:
                profile = self.market_data.get_company_profile(ticker)
                fund_result = self.fundamental.analyze(profile)
                tech_result = self.technical.analyze(profile)
                fund_result.technical_score = tech_result["score"]
                fund_result.overall_score = (
                    fund_result.fundamental_score * 0.5
                    + tech_result["score"] * 0.3
                    + fund_result.valuation_score * 0.2
                )
            except Exception as e:
                console.print(f"Erro ao analisar {ticker}: {e}", style="danger")
                return

        self._display_analysis(profile, fund_result, tech_result)

    def _cmd_compare(self, tickers: list[str]) -> None:
        """Compara empresas."""
        table = Table(title="Comparativo de Empresas")
        table.add_column("Ticker", style="cyan")
        table.add_column("Empresa")
        table.add_column("Preco")
        table.add_column("Fund.", justify="center")
        table.add_column("Tecnico", justify="center")
        table.add_column("Valuation", justify="center")
        table.add_column("Geral", justify="center")
        table.add_column("Risco")
        table.add_column("Rec.", style="bold")

        for ticker in tickers:
            with console.status(f"Analisando {ticker.upper()}..."):
                try:
                    profile = self.market_data.get_company_profile(ticker)
                    fund = self.fundamental.analyze(profile)
                    tech = self.technical.analyze(profile)
                    fund.technical_score = tech["score"]
                    fund.overall_score = (
                        fund.fundamental_score * 0.5
                        + tech["score"] * 0.3
                        + fund.valuation_score * 0.2
                    )

                    rec_style = {
                        "Compra Forte": "bold green",
                        "Compra": "green",
                        "Manter": "yellow",
                        "Venda": "red",
                        "Venda Forte": "bold red",
                    }.get(fund.recommendation.value, "white")

                    table.add_row(
                        ticker.upper(),
                        profile.name[:20],
                        f"{profile.current_price:,.2f}" if profile.current_price else "N/A",
                        f"{fund.fundamental_score:.0f}",
                        f"{tech['score']:.0f}",
                        f"{fund.valuation_score:.0f}",
                        f"{fund.overall_score:.0f}",
                        fund.risk_level.value,
                        f"[{rec_style}]{fund.recommendation.value}[/]",
                    )
                except Exception as e:
                    table.add_row(ticker.upper(), f"Erro: {e}", *["--"] * 7)

        console.print()
        console.print(table)
        console.print()

    def _cmd_technical(self, ticker: str) -> None:
        """Analise tecnica detalhada."""
        with console.status(f"Analise tecnica de {ticker.upper()}..."):
            try:
                profile = self.market_data.get_company_profile(ticker)
                report = self.technical.format_report(
                    profile, self.technical.analyze(profile)
                )
            except Exception as e:
                console.print(f"Erro: {e}", style="danger")
                return

        console.print()
        console.print(Panel(report, title=f"Analise Tecnica - {ticker.upper()}", border_style="blue"))
        console.print()

    def _cmd_portfolio(self, args: list[str]) -> None:
        """Comandos de portfolio."""
        if not args:
            console.print("Uso: /portfolio <criar|ver|add|rm|listar> ...", style="warning")
            return

        subcmd = args[0].lower()

        if subcmd == "criar":
            if len(args) < 2:
                console.print("Uso: /portfolio criar <nome> [caixa]", style="warning")
                return
            name = args[1]
            cash = float(args[2]) if len(args) > 2 else 0
            self.portfolio_mgr.create_portfolio(name, cash)
            console.print(f"Carteira '{name}' criada com sucesso!", style="success")

        elif subcmd == "ver":
            if len(args) < 2:
                console.print("Uso: /portfolio ver <nome>", style="warning")
                return
            portfolio = self.portfolio_mgr.load_portfolio(args[1])
            if not portfolio:
                console.print(f"Carteira '{args[1]}' nao encontrada.", style="warning")
                return
            with console.status("Atualizando precos..."):
                self.portfolio_mgr.update_prices(portfolio)
            self._display_portfolio(portfolio)

        elif subcmd == "add":
            if len(args) < 5:
                console.print(
                    "Uso: /portfolio add <nome> <ticker> <quantidade> <preco>",
                    style="warning",
                )
                return
            portfolio = self.portfolio_mgr.load_portfolio(args[1])
            if not portfolio:
                console.print(f"Carteira '{args[1]}' nao encontrada.", style="warning")
                return
            self.portfolio_mgr.add_position(
                portfolio, args[2], float(args[3]), float(args[4])
            )
            console.print(
                f"{args[3]} acoes de {args[2].upper()} adicionadas a carteira '{args[1]}'.",
                style="success",
            )

        elif subcmd == "rm":
            if len(args) < 3:
                console.print("Uso: /portfolio rm <nome> <ticker> [quantidade]", style="warning")
                return
            portfolio = self.portfolio_mgr.load_portfolio(args[1])
            if not portfolio:
                console.print(f"Carteira '{args[1]}' nao encontrada.", style="warning")
                return
            shares = float(args[3]) if len(args) > 3 else None
            self.portfolio_mgr.remove_position(portfolio, args[2], shares)
            console.print(f"Posicao de {args[2].upper()} removida.", style="success")

        elif subcmd == "listar":
            portfolios = self.portfolio_mgr.list_portfolios()
            if not portfolios:
                console.print("Nenhuma carteira encontrada.", style="warning")
            else:
                console.print("Carteiras salvas:", style="info")
                for name in portfolios:
                    console.print(f"  - {name}")

        else:
            console.print(f"Subcomando desconhecido: {subcmd}", style="warning")

    def _cmd_screen(self, tickers: list[str]) -> None:
        """Screening de acoes."""
        table = Table(title="Screening de Acoes (ordenado por score)")
        table.add_column("#", justify="right")
        table.add_column("Ticker", style="cyan")
        table.add_column("Empresa")
        table.add_column("Score", justify="center", style="bold")
        table.add_column("Rec.")
        table.add_column("Risco")

        results = []
        for ticker in tickers:
            with console.status(f"Analisando {ticker.upper()}..."):
                try:
                    profile = self.market_data.get_company_profile(ticker)
                    fund = self.fundamental.analyze(profile)
                    tech = self.technical.analyze(profile)
                    fund.technical_score = tech["score"]
                    fund.overall_score = (
                        fund.fundamental_score * 0.5
                        + tech["score"] * 0.3
                        + fund.valuation_score * 0.2
                    )
                    results.append((profile, fund))
                except Exception as e:
                    console.print(f"  Erro em {ticker}: {e}", style="warning")

        results.sort(key=lambda x: x[1].overall_score, reverse=True)

        for i, (profile, fund) in enumerate(results, 1):
            rec_style = {
                "Compra Forte": "bold green",
                "Compra": "green",
                "Manter": "yellow",
                "Venda": "red",
                "Venda Forte": "bold red",
            }.get(fund.recommendation.value, "white")

            table.add_row(
                str(i),
                profile.ticker,
                profile.name[:25],
                f"{fund.overall_score:.0f}",
                f"[{rec_style}]{fund.recommendation.value}[/]",
                fund.risk_level.value,
            )

        console.print()
        console.print(table)
        console.print()

    def _display_analysis(
        self, profile: CompanyProfile, fund: AnalysisResult, tech: dict
    ) -> None:
        """Exibe analise completa."""
        console.print()

        # Header
        console.print(
            Panel(
                f"[bold]{profile.name}[/] ({profile.ticker}) - "
                f"{profile.sector.value} | {profile.industry}\n"
                f"Pais: {profile.country} | Moeda: {profile.currency}",
                title="Perfil da Empresa",
                border_style="blue",
            )
        )

        # Scores
        scores_table = Table(title="Scores")
        scores_table.add_column("Categoria", style="cyan")
        scores_table.add_column("Score", justify="center")
        scores_table.add_column("Barra", min_width=20)

        for label, score in [
            ("Fundamentalista", fund.fundamental_score),
            ("Tecnico", tech["score"]),
            ("Valuation", fund.valuation_score),
            ("GERAL", fund.overall_score),
        ]:
            bar = self._score_bar(score)
            style = "bold" if label == "GERAL" else ""
            scores_table.add_row(
                f"[{style}]{label}[/]", f"[{style}]{score:.0f}/100[/]", bar
            )

        console.print(scores_table)

        # Recomendacao
        rec_colors = {
            "Compra Forte": "green",
            "Compra": "green",
            "Manter": "yellow",
            "Venda": "red",
            "Venda Forte": "red",
        }
        rec_color = rec_colors.get(fund.recommendation.value, "white")
        console.print(
            Panel(
                f"[bold {rec_color}]{fund.recommendation.value}[/]\n"
                f"Risco: {fund.risk_level.value}",
                title="Recomendacao",
                border_style=rec_color,
            )
        )

        # Metricas-chave
        if fund.key_metrics:
            metrics_table = Table(title="Metricas-Chave")
            metrics_table.add_column("Metrica", style="cyan")
            metrics_table.add_column("Valor", justify="right")
            for key, val in fund.key_metrics.items():
                metrics_table.add_row(key, str(val))
            console.print(metrics_table)

        # Pontos fortes e fracos
        if fund.strengths:
            console.print("\n[green]Pontos Fortes:[/]")
            for s in fund.strengths:
                console.print(f"  [green]+[/] {s}")
        if fund.weaknesses:
            console.print("\n[red]Pontos Fracos:[/]")
            for w in fund.weaknesses:
                console.print(f"  [red]-[/] {w}")

        # Sinais tecnicos
        if tech.get("signals"):
            console.print(f"\n[blue]Veredicto Tecnico:[/] {tech['verdict']}")
            for sig in tech["signals"][:5]:
                color = {"ALTA": "green", "OPORTUNIDADE": "green", "BAIXA": "red",
                         "ATENCAO": "yellow", "RISCO": "red"}.get(sig["tipo"], "white")
                console.print(f"  [{color}][{sig['tipo']}][/] {sig['indicador']}: {sig['descricao']}")

        console.print()

    def _display_portfolio(self, portfolio: Portfolio) -> None:
        """Exibe carteira."""
        summary = self.portfolio_mgr.get_portfolio_summary(portfolio)

        console.print()
        gl_color = "green" if summary["lucro_prejuizo_total"] >= 0 else "red"
        console.print(
            Panel(
                f"Caixa: ${summary['caixa']:,.2f}\n"
                f"Total Investido: ${summary['total_investido']:,.2f}\n"
                f"Valor Atual: ${summary['valor_total']:,.2f}\n"
                f"[{gl_color}]Lucro/Prejuizo: ${summary['lucro_prejuizo_total']:,.2f} "
                f"({summary['lucro_prejuizo_total_pct']:+.2f}%)[/]",
                title=f"Carteira: {portfolio.name}",
                border_style="cyan",
            )
        )

        if summary["posicoes"]:
            table = Table(title="Posicoes")
            table.add_column("Ticker", style="cyan")
            table.add_column("Empresa")
            table.add_column("Qtd", justify="right")
            table.add_column("PM", justify="right")
            table.add_column("Atual", justify="right")
            table.add_column("Valor", justify="right")
            table.add_column("L/P", justify="right")
            table.add_column("L/P %", justify="right")

            for pos in summary["posicoes"]:
                lp_color = "green" if pos["lucro_prejuizo"] >= 0 else "red"
                table.add_row(
                    pos["ticker"],
                    pos["empresa"][:18],
                    f"{pos['quantidade']:.0f}",
                    f"${pos['preco_medio']:,.2f}",
                    f"${pos['preco_atual']:,.2f}",
                    f"${pos['valor_atual']:,.2f}",
                    f"[{lp_color}]${pos['lucro_prejuizo']:,.2f}[/]",
                    f"[{lp_color}]{pos['lucro_prejuizo_pct']:+.2f}%[/]",
                )

            console.print(table)

        if summary["alocacao_por_setor"]:
            sector_table = Table(title="Alocacao por Setor")
            sector_table.add_column("Setor", style="cyan")
            sector_table.add_column("Alocacao %", justify="right")
            for sector, pct in sorted(
                summary["alocacao_por_setor"].items(), key=lambda x: x[1], reverse=True
            ):
                sector_table.add_row(sector, f"{pct:.1f}%")
            console.print(sector_table)

        console.print()

    @staticmethod
    def _score_bar(score: float, width: int = 20) -> str:
        filled = int(score / 100 * width)
        empty = width - filled
        if score >= 70:
            color = "green"
        elif score >= 45:
            color = "yellow"
        else:
            color = "red"
        return f"[{color}]{'█' * filled}{'░' * empty}[/]"
