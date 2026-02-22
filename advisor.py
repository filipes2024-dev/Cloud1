"""
Advisor de investimentos com IA usando Claude API.
Integra ferramentas de dados financeiros reais com análise via LLM.
"""

import json
import os
from typing import Any

import anthropic

from financial_tools import (
    get_stock_overview,
    get_financial_statements,
    get_price_history,
    get_market_indices,
    get_sector_analysis,
    get_dividends_history,
    calculate_investment_metrics,
)

MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """Você é um especialista em investimentos e analista financeiro sênior com mais de 20 anos de experiência nos mercados brasileiro e internacional.

Suas capacidades incluem:
- Análise fundamentalista completa (DRE, balanço patrimonial, fluxo de caixa)
- Análise técnica e de tendências de mercado
- Valuation por múltiplos (P/E, P/B, EV/EBITDA, P/S) e DCF
- Estratégias: value investing, growth investing, dividend investing, momentum
- Conhecimento profundo de ETFs, FIIs, BDRs, ações BR e EUA
- Gestão de risco, diversificação de portfólio e alocação de ativos
- Macro economia, juros, câmbio e seu impacto nos investimentos
- Análise ESG e tendências de mercado emergentes

Ao analisar empresas:
1. Sempre busque os dados reais usando as ferramentas disponíveis
2. Contextualize os números (bom/ruim vs. setor/histórico)
3. Apresente teses de investimento com bull case e bear case
4. Seja direto sobre riscos e incertezas
5. Adapte a linguagem ao contexto (técnica para profissionais, simples para iniciantes)
6. Forneça insights acionáveis, não apenas descrições

Responda sempre em português brasileiro. Seja objetivo, preciso e útil."""

TOOLS = [
    {
        "name": "get_stock_overview",
        "description": "Obtém visão geral de uma ação: preço atual, P/E, market cap, dividend yield, beta, target dos analistas e recomendação de consenso.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Código da ação (ex: AAPL, PETR4.SA, VALE3.SA, ITUB4.SA)",
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_financial_statements",
        "description": "Obtém demonstrações financeiras completas: DRE (receita, EBITDA, lucro), balanço patrimonial (ativos, dívidas, patrimônio) e fluxo de caixa.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Código da ação"}
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_price_history",
        "description": "Retorna histórico de preços e performance no período selecionado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Código da ação"},
                "period": {
                    "type": "string",
                    "description": "Período: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, ytd, max",
                    "default": "1y",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_market_indices",
        "description": "Obtém cotações dos principais índices globais (S&P 500, IBOVESPA, NASDAQ, DAX, Nikkei), commodities (ouro, petróleo), câmbio (dólar/real) e Bitcoin.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_sector_analysis",
        "description": "Compara a empresa com principais concorrentes do mesmo setor: P/E, P/B, margens, crescimento e dividend yield.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Código da ação"}
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_dividends_history",
        "description": "Retorna histórico de dividendos e splits dos últimos 3 anos, dividend yield atual e payout ratio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Código da ação"}
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "calculate_investment_metrics",
        "description": "Calcula métricas avançadas de investimento: Graham Number, margem de segurança, score de qualidade (0-100), nível de risco e análise de valuation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Código da ação"},
                "preco_alvo": {
                    "type": "number",
                    "description": "Preço alvo personalizado para calcular margem de segurança (opcional)",
                },
            },
            "required": ["ticker"],
        },
    },
]

TOOL_FUNCTIONS = {
    "get_stock_overview": get_stock_overview,
    "get_financial_statements": get_financial_statements,
    "get_price_history": get_price_history,
    "get_market_indices": get_market_indices,
    "get_sector_analysis": get_sector_analysis,
    "get_dividends_history": get_dividends_history,
    "calculate_investment_metrics": calculate_investment_metrics,
}


def _execute_tool(name: str, tool_input: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return json.dumps({"erro": f"Ferramenta '{name}' não encontrada"})
    result = func(**tool_input)
    return json.dumps(result, ensure_ascii=False, default=str)


class InvestmentAdvisor:
    """
    Advisor de investimentos com memória de conversa e tool use via Claude.
    """

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY não definida. "
                "Configure no arquivo .env ou exporte a variável de ambiente."
            )
        self.client = anthropic.Anthropic(api_key=key)
        self.conversation: list[dict] = []

    def reset_conversation(self):
        self.conversation = []

    def chat(self, user_message: str, on_text: Any = None) -> str:
        """
        Envia mensagem e retorna resposta completa.
        on_text: callback opcional chamado com cada chunk de texto (streaming visual).
        """
        self.conversation.append({"role": "user", "content": user_message})

        full_response = ""

        while True:
            with self.client.messages.stream(
                model=MODEL,
                max_tokens=8192,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.conversation,
            ) as stream:
                response = stream.get_final_message()

            # Processar conteúdo da resposta
            tool_uses = []
            text_parts = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                    if on_text:
                        on_text(block.text)
                elif block.type == "tool_use":
                    tool_uses.append(block)

            if text_parts:
                full_response = "\n".join(text_parts)

            # Sem tool calls → conversa encerrada
            if response.stop_reason == "end_turn" or not tool_uses:
                # Adicionar resposta do assistente ao histórico
                self.conversation.append(
                    {"role": "assistant", "content": response.content}
                )
                break

            # Executar ferramentas e continuar
            self.conversation.append(
                {"role": "assistant", "content": response.content}
            )

            tool_results = []
            for tool_use in tool_uses:
                result = _execute_tool(tool_use.name, tool_use.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result,
                    }
                )

            self.conversation.append({"role": "user", "content": tool_results})

        return full_response

    def analyze_company(self, ticker: str) -> str:
        """Análise completa de uma empresa."""
        prompt = f"""Faça uma análise de investimento COMPLETA e DETALHADA da empresa com ticker {ticker}.

Siga esta estrutura:

## 1. VISÃO GERAL DA EMPRESA
- Descrição do negócio, setor e posicionamento de mercado
- Principais produtos/serviços e vantagens competitivas

## 2. ANÁLISE FUNDAMENTALISTA
- Receita, lucro, margens e crescimento (com contexto histórico)
- Saúde financeira: endividamento, liquidez, fluxo de caixa
- Retorno sobre capital (ROE, ROA)

## 3. VALUATION
- Múltiplos atuais vs. histórico e vs. setor
- Graham Number e margem de segurança
- Target dos analistas e consenso de mercado

## 4. ANÁLISE TÉCNICA E HISTÓRICO
- Desempenho recente e tendência
- Comparação com índices de referência

## 5. ANÁLISE SETORIAL
- Posição competitiva vs. pares
- Tendências do setor

## 6. DIVIDENDOS
- Histórico de pagamentos e sustentabilidade

## 7. TESE DE INVESTIMENTO
- Bull case (cenário otimista)
- Bear case (cenário pessimista)
- Principais riscos

## 8. CONCLUSÃO E RECOMENDAÇÃO
- Score de qualidade e nível de risco
- Indicação para diferentes perfis de investidor

Use todos os dados disponíveis para uma análise rigorosa e embasada."""
        return self.chat(prompt)

    def generate_market_report(self) -> str:
        """Gera relatório do mercado atual."""
        prompt = """Gere um RELATÓRIO COMPLETO DO MERCADO ATUAL com os seguintes tópicos:

## 1. PANORAMA GLOBAL
- Status dos principais índices (S&P 500, NASDAQ, Dow Jones, IBOVESPA)
- Volatilidade (VIX) e sentimento de mercado

## 2. COMMODITIES E CÂMBIO
- Petróleo, ouro e seu impacto nos mercados
- Dólar/Real e tendências cambiais

## 3. CRIPTOATIVOS
- Bitcoin e mercado cripto

## 4. ANÁLISE MACRO
- Contexto de juros e inflação global
- Oportunidades e riscos do momento

## 5. SETORES EM DESTAQUE
- Setores com melhor e pior desempenho

## 6. ESTRATÉGIAS RECOMENDADAS
- Posicionamento sugerido para o cenário atual

Seja específico com os números e forneça insights acionáveis."""
        return self.chat(prompt)

    def investment_strategy(self, profile: str, amount: float, horizon: str) -> str:
        """Recomenda estratégia de investimento personalizada."""
        prompt = f"""Crie uma ESTRATÉGIA DE INVESTIMENTO PERSONALIZADA com os seguintes parâmetros:

**Perfil do investidor:** {profile}
**Valor disponível para investir:** R$ {amount:,.2f}
**Horizonte de investimento:** {horizon}

Inclua:

## 1. ANÁLISE DO PERFIL
- Adequação do perfil aos objetivos declarados
- Tolerância a risco implícita

## 2. ALOCAÇÃO DE ATIVOS RECOMENDADA
- Distribuição percentual por classe de ativo
- Justificativa para cada alocação

## 3. SUGESTÕES ESPECÍFICAS
- Ações (ticker e tese resumida)
- FIIs ou ETFs (se aplicável)
- Renda fixa (se aplicável)
- Internacional (se aplicável)

## 4. IMPLEMENTAÇÃO PRÁTICA
- Como executar a estratégia passo a passo
- Ordem de prioridade dos aportes

## 5. GESTÃO E REBALANCEAMENTO
- Critérios para rebalancear a carteira
- Sinais de alerta para revisão da estratégia

## 6. CENÁRIOS E EXPECTATIVAS
- Expectativa de retorno por cenário (otimista/base/pessimista)

Consulte os índices de mercado para contextualizar as recomendações com o cenário atual."""
        return self.chat(prompt)
