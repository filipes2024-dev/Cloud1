# Investment Analysis Framework

Assistente inteligente de investimentos com IA (Claude Opus 4.6) e dados financeiros em tempo real.

## Funcionalidades

- **Análise completa de empresas** — fundamentalista, técnica, valuation e recomendação
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
# Menu interativo
python main.py

# Análise direta de uma ação
python main.py --analyze AAPL
python main.py --analyze PETR4.SA
python main.py --analyze VALE3.SA

# Relatório do mercado atual
python main.py --market

# Chat livre com o advisor
python main.py --chat
```

## Exemplos de perguntas no chat

- "Analise NVDA para mim e diga se vale comprar"
- "Compare ITUB4.SA com BBDC4.SA"
- "Qual a melhor estratégia para investir R$ 50.000 com perfil conservador?"
- "O que é value investing e como aplicar no Brasil?"
- "Quais setores tendem a se beneficiar com juros altos?"
- "Explique o Graham Number e como usá-lo"
- "Analise o risco de concentrar a carteira em tecnologia"

## Estrutura do Projeto

```
Cloud1/
├── main.py              # CLI principal (entry point)
├── advisor.py           # Integração Claude API + tool use
├── financial_tools.py   # Ferramentas de dados (yfinance)
├── report_generator.py  # Formatação de relatórios (Rich)
├── requirements.txt     # Dependências Python
├── .env.example         # Template de configuração
└── reports/             # Relatórios gerados (criado automaticamente)
```

## Arquitetura

```
Usuário
   ↓
main.py (CLI)
   ↓
advisor.py (InvestmentAdvisor)
   ├── Claude Opus 4.6 (claude-opus-4-6)
   │   ├── Adaptive Thinking
   │   └── Streaming
   └── Tool Use (agentic loop)
       ├── get_stock_overview
       ├── get_financial_statements
       ├── get_price_history
       ├── get_market_indices
       ├── get_sector_analysis
       ├── get_dividends_history
       └── calculate_investment_metrics
           └── financial_tools.py (yfinance)
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
