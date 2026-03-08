"""
Advisor de investimentos com IA usando DeepSeek API.
Integra ferramentas de dados financeiros reais com análise via LLM.
"""

import json
import os
from typing import Any

from openai import OpenAI

from financial_tools import (
    get_stock_overview,
    get_financial_statements,
    get_price_history,
    get_market_indices,
    get_sector_analysis,
    get_dividends_history,
    calculate_investment_metrics,
    get_technical_indicators,
)
from stock_screener import screen_stocks
from portfolio_analyzer import analyze_portfolio

MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com"

SYSTEM_PROMPT = """Você é um especialista em investimentos e analista financeiro sênior com mais de 20 anos de experiência nos mercados brasileiro e internacional.

Suas capacidades incluem:
- Análise fundamentalista completa (DRE, balanço patrimonial, fluxo de caixa)
- Análise técnica avançada (RSI, MACD, Bollinger Bands, médias móveis, suportes/resistências)
- Valuation por múltiplos (P/E, P/B, EV/EBITDA, P/S) e DCF
- Estratégias: value investing, growth investing, dividend investing, momentum
- Conhecimento profundo de ETFs, FIIs, BDRs, ações BR e EUA
- Gestão de risco, diversificação de portfólio e alocação de ativos
- Macro economia, juros, câmbio e seu impacto nos investimentos
- Stock screening: filtrar ações por critérios (valor, crescimento, dividendos, momentum, qualidade)
- Análise de portfólio: correlação, diversificação, risco, Sharpe ratio e sugestões de rebalanceamento

Ao analisar empresas:
1. Sempre busque os dados reais usando as ferramentas disponíveis
2. Use indicadores técnicos (RSI, MACD, Bollinger) para complementar a análise fundamentalista
3. Contextualize os números (bom/ruim vs. setor/histórico)
4. Apresente teses de investimento com bull case e bear case
5. Seja direto sobre riscos e incertezas
6. Adapte a linguagem ao contexto (técnica para profissionais, simples para iniciantes)
7. Forneça insights acionáveis, não apenas descrições
8. Quando pedirem dicas de investimento, use o screener para encontrar oportunidades reais

Ao recomendar ações:
- Use o screener para filtrar oportunidades por estratégia
- Combine análise fundamentalista com análise técnica
- Sempre mencione riscos e que resultados passados não garantem retornos futuros

Responda sempre em português brasileiro. Seja objetivo, preciso e útil."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_overview",
            "description": "Obtém visão geral de uma ação: preço atual, P/E, market cap, dividend yield, beta, target dos analistas e recomendação de consenso.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_statements",
            "description": "Obtém demonstrações financeiras completas: DRE (receita, EBITDA, lucro), balanço patrimonial (ativos, dívidas, patrimônio) e fluxo de caixa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Código da ação"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "Retorna histórico de preços e performance no período selecionado.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_indices",
            "description": "Obtém cotações dos principais índices globais (S&P 500, IBOVESPA, NASDAQ, DAX, Nikkei), commodities (ouro, petróleo), câmbio (dólar/real) e Bitcoin.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sector_analysis",
            "description": "Compara a empresa com principais concorrentes do mesmo setor: P/E, P/B, margens, crescimento e dividend yield.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Código da ação"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dividends_history",
            "description": "Retorna histórico de dividendos e splits dos últimos 3 anos, dividend yield atual e payout ratio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Código da ação"}
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_investment_metrics",
            "description": "Calcula métricas avançadas de investimento: Graham Number, margem de segurança, score de qualidade (0-100), nível de risco e análise de valuation.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_indicators",
            "description": "Calcula indicadores técnicos completos: RSI (14), MACD (12,26,9), Bollinger Bands (20,2), médias móveis (SMA 20/50/200), suportes/resistências, sinais de trading e tendência geral.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Código da ação"},
                    "period": {
                        "type": "string",
                        "description": "Período de análise: 3mo, 6mo, 1y, 2y (padrão: 6mo)",
                        "default": "6mo",
                    },
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "screen_stocks",
            "description": "Filtra e rankeia ações por estratégia de investimento. Estratégias: 'value' (baixo P/E e P/B), 'growth' (alto crescimento), 'dividend' (alto yield), 'momentum' (tendência de alta), 'quality' (alto ROE e margens), 'undervalued' (preço abaixo do justo). Mercados: 'us' (EUA), 'br' (Brasil), 'fiis' (FIIs brasileiros).",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "description": "Estratégia: value, growth, dividend, momentum, quality, undervalued",
                    },
                    "market": {
                        "type": "string",
                        "description": "Mercado: us, br, fiis (padrão: us)",
                        "default": "us",
                    },
                    "custom_tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tickers personalizada (opcional, sobrescreve market)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de resultados (padrão: 10)",
                        "default": 10,
                    },
                },
                "required": ["strategy"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_portfolio",
            "description": "Analisa uma carteira de investimentos: retorno, volatilidade, Sharpe ratio, correlação entre ativos, diversificação, max drawdown e sugestões de melhoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tickers da carteira (mínimo 2)",
                    },
                    "weights": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Pesos de cada ativo (devem somar 1.0). Se omitido, assume pesos iguais.",
                    },
                    "period": {
                        "type": "string",
                        "description": "Período de análise: 1mo, 3mo, 6mo, 1y, 2y, 5y (padrão: 1y)",
                        "default": "1y",
                    },
                },
                "required": ["tickers"],
            },
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
    "get_technical_indicators": get_technical_indicators,
    "screen_stocks": screen_stocks,
    "analyze_portfolio": analyze_portfolio,
}


def _execute_tool(name: str, tool_input: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return json.dumps({"erro": f"Ferramenta '{name}' não encontrada"})
    result = func(**tool_input)
    return json.dumps(result, ensure_ascii=False, default=str)


class InvestmentAdvisor:
    """
    Advisor de investimentos com memória de conversa e tool use via DeepSeek.
    """

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise ValueError(
                "DEEPSEEK_API_KEY não definida. "
                "Configure no arquivo .env ou exporte a variável de ambiente."
            )
        self.client = OpenAI(api_key=key, base_url=BASE_URL)
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
            response = self.client.chat.completions.create(
                model=MODEL,
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *self.conversation,
                ],
                tools=TOOLS,
            )

            message = response.choices[0].message

            # Extrair texto da resposta
            if message.content:
                full_response = message.content
                if on_text:
                    on_text(message.content)

            # Sem tool calls → conversa encerrada
            if not message.tool_calls:
                self.conversation.append(
                    {"role": "assistant", "content": message.content or ""}
                )
                break

            # Adicionar resposta do assistente (com tool_calls) ao histórico
            self.conversation.append(message.model_dump())

            # Executar ferramentas e adicionar resultados
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                result = _execute_tool(func_name, func_args)

                self.conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

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
