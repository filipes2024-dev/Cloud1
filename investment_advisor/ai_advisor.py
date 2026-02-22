"""Assessor de investimentos com IA integrada ao Claude."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from .fundamental_analysis import FundamentalAnalyzer
from .market_data import MarketDataProvider
from .models import AnalysisResult, CompanyProfile, Portfolio
from .portfolio_manager import PortfolioManager
from .technical_analysis import TechnicalAnalyzer

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Voce e um assessor de investimentos de alto nivel, especialista em mercado financeiro global.
Voce ajuda investidores a tomar decisoes fundamentadas com base em dados reais de mercado.

Suas competencias:
- Analise fundamentalista (balancos, DRE, indicadores financeiros)
- Analise tecnica (tendencias, suportes, resistencias, indicadores)
- Valuation (multiplos, DCF, comparativos setoriais)
- Gestao de portfolio (diversificacao, alocacao de ativos, risco)
- Estrategias de investimento (value investing, growth, dividendos, momentum)
- Macroeconomia e impacto nos mercados

Diretrizes:
1. Sempre baseie suas recomendacoes em dados concretos quando disponiveis
2. Apresente tanto os pontos positivos quanto os riscos
3. Nunca garanta retornos - investimentos envolvem risco
4. Adapte a linguagem ao nivel do investidor
5. Quando analisar empresas, use os dados fornecidos pelas ferramentas
6. Para perguntas gerais de estrategia, use seu conhecimento de mercado
7. Responda sempre em portugues brasileiro
8. Seja direto e objetivo, mas completo nas analises

Voce tem acesso a ferramentas para buscar dados de mercado em tempo real,
analisar empresas e gerenciar portfolios. Use-as quando o usuario pedir
informacoes sobre ativos especificos.
"""


class AIAdvisor:
    """Assessor de investimentos com IA (Claude)."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.market_data = MarketDataProvider()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.portfolio_manager = PortfolioManager()
        self.conversation_history: list[dict] = []
        self.tools = self._define_tools()

    def _define_tools(self) -> list[dict]:
        """Define ferramentas disponiveis para o Claude."""
        return [
            {
                "name": "analyze_company",
                "description": (
                    "Analisa uma empresa de forma completa (fundamentalista + tecnica). "
                    "Retorna scores, recomendacao, pontos fortes/fracos e metricas-chave. "
                    "Use para qualquer ticker de acao (ex: AAPL, MSFT, PETR4.SA)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": (
                                "Ticker da acao (ex: AAPL, GOOGL, PETR4.SA para acoes brasileiras)"
                            ),
                        }
                    },
                    "required": ["ticker"],
                },
            },
            {
                "name": "compare_companies",
                "description": (
                    "Compara multiplas empresas lado a lado com analise fundamentalista e tecnica."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tickers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista de tickers para comparar (ex: ['AAPL', 'MSFT', 'GOOGL'])",
                        }
                    },
                    "required": ["tickers"],
                },
            },
            {
                "name": "get_portfolio_analysis",
                "description": (
                    "Busca e analisa a carteira do usuario, incluindo alocacao, "
                    "performance e sugestoes."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "portfolio_name": {
                            "type": "string",
                            "description": "Nome da carteira",
                        }
                    },
                    "required": ["portfolio_name"],
                },
            },
            {
                "name": "screen_stocks",
                "description": (
                    "Analisa uma lista de acoes e rankeia por score. "
                    "Util para encontrar as melhores oportunidades em um grupo de ativos."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tickers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista de tickers para analisar",
                        }
                    },
                    "required": ["tickers"],
                },
            },
        ]

    def chat(self, user_message: str) -> str:
        """Envia mensagem ao assessor e retorna resposta."""
        self.conversation_history.append({"role": "user", "content": user_message})

        messages = self.conversation_history.copy()

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                thinking={"type": "adaptive"},
                tools=self.tools,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                assistant_text = self._extract_text(response)
                self.conversation_history.append(
                    {"role": "assistant", "content": response.content}
                )
                return assistant_text

            # Process tool calls
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks:
                assistant_text = self._extract_text(response)
                self.conversation_history.append(
                    {"role": "assistant", "content": response.content}
                )
                return assistant_text

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_block in tool_use_blocks:
                result = self._execute_tool(tool_block.name, tool_block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

        # Unreachable but satisfies type checker
        return ""

    def analyze_company(self, ticker: str) -> dict[str, Any]:
        """Analisa uma empresa e retorna dados completos."""
        profile = self.market_data.get_company_profile(ticker)
        fundamental = self.fundamental_analyzer.analyze(profile)
        technical = self.technical_analyzer.analyze(profile)

        fundamental.technical_score = technical["score"]
        fundamental.overall_score = (
            fundamental.fundamental_score * 0.5
            + technical["score"] * 0.3
            + fundamental.valuation_score * 0.2
        )

        return {
            "perfil": {
                "ticker": profile.ticker,
                "nome": profile.name,
                "setor": profile.sector.value,
                "industria": profile.industry,
                "pais": profile.country,
                "preco_atual": profile.current_price,
                "preco_alvo": profile.target_price,
                "descricao": profile.description[:500] if profile.description else "",
            },
            "analise_fundamentalista": fundamental.to_report_dict(),
            "analise_tecnica": technical,
        }

    def compare_companies(self, tickers: list[str]) -> list[dict]:
        """Compara multiplas empresas."""
        results = []
        for ticker in tickers:
            try:
                analysis = self.analyze_company(ticker)
                results.append(analysis)
            except Exception as e:
                results.append({"ticker": ticker, "erro": str(e)})
        return results

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Executa uma ferramenta e retorna resultado como string."""
        try:
            if tool_name == "analyze_company":
                result = self.analyze_company(tool_input["ticker"])
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)

            elif tool_name == "compare_companies":
                result = self.compare_companies(tool_input["tickers"])
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)

            elif tool_name == "get_portfolio_analysis":
                portfolio = self.portfolio_manager.load_portfolio(tool_input["portfolio_name"])
                if portfolio is None:
                    return json.dumps({
                        "erro": f"Carteira '{tool_input['portfolio_name']}' nao encontrada. "
                        f"Carteiras disponiveis: {self.portfolio_manager.list_portfolios()}"
                    })
                self.portfolio_manager.update_prices(portfolio)
                summary = self.portfolio_manager.get_portfolio_summary(portfolio)
                return json.dumps(summary, ensure_ascii=False, indent=2, default=str)

            elif tool_name == "screen_stocks":
                results = []
                for ticker in tool_input["tickers"]:
                    try:
                        profile = self.market_data.get_company_profile(ticker)
                        fundamental = self.fundamental_analyzer.analyze(profile)
                        technical = self.technical_analyzer.analyze(profile)
                        fundamental.technical_score = technical["score"]
                        fundamental.overall_score = (
                            fundamental.fundamental_score * 0.5
                            + technical["score"] * 0.3
                            + fundamental.valuation_score * 0.2
                        )
                        results.append(fundamental.to_report_dict())
                    except Exception as e:
                        results.append({"ticker": ticker, "erro": str(e)})

                results.sort(
                    key=lambda x: x.get("score_geral", 0),
                    reverse=True,
                )
                return json.dumps(results, ensure_ascii=False, indent=2, default=str)

            return json.dumps({"erro": f"Ferramenta desconhecida: {tool_name}"})

        except Exception as e:
            logger.error("Erro ao executar ferramenta %s: %s", tool_name, e)
            return json.dumps({"erro": str(e)}, ensure_ascii=False)

    @staticmethod
    def _extract_text(response) -> str:
        """Extrai texto da resposta do Claude."""
        parts = []
        for block in response.content:
            if block.type == "text":
                parts.append(block.text)
        return "\n".join(parts) if parts else ""

    def reset_conversation(self) -> None:
        """Limpa historico de conversa."""
        self.conversation_history.clear()
