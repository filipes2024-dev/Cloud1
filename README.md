# Investment Analysis Framework

Agente inteligente de investimentos com IA (Claude Opus 4.6) e dados financeiros em tempo real. Analisa empresas, filtra oportunidades, calcula indicadores técnicos e analisa portfólios.

## Funcionalidades

- **Análise completa de empresas** — fundamentalista, técnica, valuation e recomendação
- **Stock Screener** — filtra ações por estratégia: value, growth, dividend, momentum, quality, undervalued
- **Análise técnica avançada** — RSI, MACD, Bollinger Bands, médias móveis, suportes/resistências
- **Análise de portfólio** — retorno, risco, correlação, Sharpe ratio, diversificação e sugestões
- **Relatório de mercado** — índices globais, câmbio, commodities e macro
- **Estratégia personalizada** — alocação de ativos por perfil, valor e horizonte
- **Chat livre** — pergunte qualquer coisa sobre investimentos
- **Dados rápidos** — cotação, métricas e score de qualidade sem IA

## Instalação

```bash
# 1. Clone o repositório e entre na pasta
cd Cloud1

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure a API Key da Anthropic
cp .env.example .env
# Edite o .env e adicione sua chave ANTHROPIC_API_KEY
```

## Uso

```bash
# Menu interativo (todas as opções)
python main.py

# Análise completa de uma empresa (com IA)
python main.py --analyze AAPL
python main.py --analyze PETR4.SA
python main.py --analyze VALE3.SA

# Stock Screener — filtrar ações por estratégia
python main.py --screen value                         # Value investing (EUA)
python main.py --screen growth --market-filter br     # Growth (Brasil)
python main.py --screen dividend --market-filter br   # Dividendos (Brasil)
python main.py --screen momentum                      # Momentum (EUA)
python main.py --screen quality --market-filter br    # Quality (Brasil)
python main.py --screen undervalued                   # Subvalorizadas (EUA)

# Análise técnica (RSI, MACD, Bollinger)
python main.py --technical NVDA
python main.py --technical PETR4.SA

# Relatório do mercado atual
python main.py --market

# Chat livre com o advisor
python main.py --chat
```

## Exemplos de perguntas no chat

- "Analise NVDA para mim e diga se vale comprar"
- "Compare ITUB4.SA com BBDC4.SA"
- "Qual a melhor estratégia para investir R$ 50.000 com perfil conservador?"
- "Me mostre as melhores ações de dividendos do Brasil"
- "Filtre ações de crescimento nos EUA"
- "Analise os indicadores técnicos de PETR4.SA"
- "Analise minha carteira: VALE3.SA, ITUB4.SA, WEGE3.SA, PETR4.SA"
- "O que é value investing e como aplicar no Brasil?"
- "Quais setores tendem a se beneficiar com juros altos?"
- "Explique o Graham Number e como usá-lo"
- "Analise o risco de concentrar a carteira em tecnologia"

## Estrutura do Projeto

```
Cloud1/
├── main.py                # CLI principal (entry point)
├── advisor.py             # Integração Claude API + tool use (agente IA)
├── financial_tools.py     # Dados financeiros + indicadores técnicos (yfinance)
├── stock_screener.py      # Stock screener (value, growth, dividend, momentum, quality)
├── portfolio_analyzer.py  # Análise de portfólio (correlação, risco, Sharpe)
├── report_generator.py    # Formatação de relatórios (Rich)
├── requirements.txt       # Dependências Python
├── .env.example           # Template de configuração
└── reports/               # Relatórios gerados (criado automaticamente)
```

## Arquitetura

```
Usuário
   ↓
main.py (CLI — menu interativo + args)
   ↓
advisor.py (InvestmentAdvisor — agente IA)
   ├── Claude Opus 4.6 (claude-opus-4-6)
   │   ├── Adaptive Thinking
   │   └── Streaming
   └── Tool Use (agentic loop — 10 ferramentas)
       │
       ├── financial_tools.py (yfinance)
       │   ├── get_stock_overview
       │   ├── get_financial_statements
       │   ├── get_price_history
       │   ├── get_market_indices
       │   ├── get_sector_analysis
       │   ├── get_dividends_history
       │   ├── calculate_investment_metrics
       │   └── get_technical_indicators  ← NOVO
       │
       ├── stock_screener.py             ← NOVO
       │   └── screen_stocks (value/growth/dividend/momentum/quality/undervalued)
       │
       └── portfolio_analyzer.py         ← NOVO
           └── analyze_portfolio (retorno/risco/correlação/Sharpe/diversificação)
```

## Obtendo a API Key

1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Crie uma conta ou faça login
3. Gere uma API Key em Settings > API Keys
4. Adicione no arquivo `.env`

## Tickers Suportados

- **Ações EUA**: AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, etc.
- **Ações Brasil**: PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA, WEGE3.SA, etc.
- **FIIs**: HGLG11.SA, KNRI11.SA, MXRF11.SA, etc.
- **ETFs**: SPY, QQQ, VTI, BOVA11.SA, etc.
- **Índices**: ^GSPC, ^BVSP, ^IXIC, etc.
