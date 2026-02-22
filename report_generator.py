"""
Gerador de relatórios de investimento em Markdown e console (Rich).
"""

import os
from datetime import datetime
from pathlib import Path


def save_markdown_report(content: str, title: str, ticker: str = "") -> str:
    """
    Salva relatório em arquivo Markdown.
    Retorna o caminho do arquivo gerado.
    """
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = ticker.upper() if ticker else title.lower().replace(" ", "_")[:30]
    filename = f"{slug}_{timestamp}.md"
    filepath = reports_dir / filename

    header = f"""# {title}

> Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}
> Ferramenta: Investment Analysis Framework - Powered by Claude Opus 4.6

---

"""
    full_content = header + content

    filepath.write_text(full_content, encoding="utf-8")
    return str(filepath)


def print_welcome():
    """Exibe banner de boas-vindas."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console()
        title = Text()
        title.append("Investment Analysis Framework", style="bold green")
        title.append("\n")
        title.append("Powered by Claude Opus 4.6 + Dados Financeiros em Tempo Real", style="dim")

        console.print(Panel(title, border_style="green", padding=(1, 4)))
        console.print()
    except ImportError:
        print("=" * 60)
        print("  Investment Analysis Framework")
        print("  Powered by Claude Opus 4.6")
        print("=" * 60)
        print()


def print_menu(options: dict[str, str]):
    """Exibe menu formatado."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(show_header=False, border_style="blue", padding=(0, 2))
        table.add_column("Opção", style="cyan bold", width=4)
        table.add_column("Descrição", style="white")

        for key, desc in options.items():
            table.add_row(key, desc)

        console.print(table)
    except ImportError:
        for key, desc in options.items():
            print(f"  [{key}] {desc}")


def print_response(text: str, title: str = "Resposta do Advisor"):
    """Exibe resposta formatada com Rich Markdown."""
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        from rich.panel import Panel

        console = Console()
        md = Markdown(text)
        console.print(Panel(md, title=f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))
    except ImportError:
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
        print(text)
        print()


def print_streaming_start(message: str = "Analisando..."):
    """Exibe indicador de loading."""
    try:
        from rich.console import Console
        console = Console()
        console.print(f"\n[bold yellow]⚡ {message}[/bold yellow]\n")
    except ImportError:
        print(f"\n{message}\n")


def print_success(message: str):
    try:
        from rich.console import Console
        Console().print(f"[bold green]✓ {message}[/bold green]")
    except ImportError:
        print(f"✓ {message}")


def print_error(message: str):
    try:
        from rich.console import Console
        Console().print(f"[bold red]✗ Erro: {message}[/bold red]")
    except ImportError:
        print(f"Erro: {message}")


def print_info(message: str):
    try:
        from rich.console import Console
        Console().print(f"[dim]{message}[/dim]")
    except ImportError:
        print(message)


def format_currency(value, currency: str = "USD") -> str:
    if value is None:
        return "N/A"
    try:
        v = float(value)
        if abs(v) >= 1e12:
            return f"{currency} {v/1e12:.2f}T"
        elif abs(v) >= 1e9:
            return f"{currency} {v/1e9:.2f}B"
        elif abs(v) >= 1e6:
            return f"{currency} {v/1e6:.2f}M"
        else:
            return f"{currency} {v:,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def print_stock_summary(data: dict):
    """Exibe resumo rápido de uma ação no console."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(
            title=f"[bold]{data.get('nome', data.get('ticker', ''))}[/bold] ({data.get('ticker', '')})",
            border_style="blue",
        )
        table.add_column("Indicador", style="cyan")
        table.add_column("Valor", style="white")

        price = data.get("preco_atual")
        change = data.get("variacao_pct")
        change_style = "green" if (change or 0) >= 0 else "red"
        change_str = f"[{change_style}]{change:+.2f}%[/{change_style}]" if change else "N/A"

        rows = [
            ("Preço", f"{price} ({change_str})" if price else "N/A"),
            ("Market Cap", format_currency(data.get("market_cap"))),
            ("P/E Ratio", str(round(data.get("pe_ratio", 0), 2)) if data.get("pe_ratio") else "N/A"),
            ("Dividend Yield", f"{data.get('dividend_yield', 0)*100:.2f}%" if data.get("dividend_yield") else "N/A"),
            ("Beta", str(data.get("beta", "N/A"))),
            ("52w Max/Min", f"{data.get('52w_high')} / {data.get('52w_low')}"),
            ("Target Analistas", str(data.get("target_price", "N/A"))),
            ("Recomendação", str(data.get("recomendacao", "N/A")).upper()),
            ("Setor", data.get("setor", "N/A")),
        ]

        for label, value in rows:
            table.add_row(label, value)

        console.print(table)
    except ImportError:
        print(f"\n{data.get('nome', '')} ({data.get('ticker', '')})")
        print(f"Preço: {data.get('preco_atual')} ({data.get('variacao_pct', 0):+.2f}%)")
        print(f"Market Cap: {format_currency(data.get('market_cap'))}")
        print(f"P/E: {data.get('pe_ratio', 'N/A')}")
