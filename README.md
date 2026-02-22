# Investment AI Advisor

Framework de assessoria de investimentos com IA integrada (Claude) para analise de empresas e tomada de decisoes.

## Funcionalidades

- **Analise Fundamentalista** - Avalia lucratividade, saude financeira, valuation e dividendos
- **Analise Tecnica** - RSI, MACD, Medias Moveis, Bollinger Bands, volatilidade
- **Assessor IA (Claude)** - Converse sobre estrategias de investimento com IA de alto nivel
- **Gestao de Portfolio** - Crie e acompanhe suas carteiras de investimento
- **Screening de Acoes** - Compare e ranqueie ativos por score
- **Dados em Tempo Real** - Integrado com Yahoo Finance para dados atualizados

## Instalacao

```bash
# Clone o repositorio
git clone <repo-url>
cd Cloud1

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instale as dependencias
pip install -e .
```

## Configuracao

Defina sua API key do Claude:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Uso

### Interface Interativa (Recomendado)

```bash
python -m investment_advisor.main
# ou
investment-advisor
```

Isso abre um chat interativo onde voce pode:

- Fazer perguntas sobre investimentos em linguagem natural
- Usar comandos especiais para analises rapidas

### Comandos da CLI Interativa

| Comando | Descricao |
|---------|-----------|
| `/analisar AAPL` | Analise completa de uma empresa |
| `/comparar AAPL MSFT GOOGL` | Compara empresas lado a lado |
| `/tecnica PETR4.SA` | Analise tecnica detalhada |
| `/screen AAPL MSFT GOOGL AMZN` | Ranking por score |
| `/portfolio criar minha_carteira` | Cria carteira |
| `/portfolio add minha_carteira AAPL 10 150` | Adiciona 10 acoes da AAPL a $150 |
| `/portfolio ver minha_carteira` | Visualiza carteira atualizada |
| `/ajuda` | Lista todos os comandos |

### Exemplos de Perguntas para a IA

```
> Qual a melhor estrategia para investir em dividendos no Brasil?
> Analise a Apple e me diga se vale a pena comprar agora
> Compare Vale e Petrobras para investimento de longo prazo
> Monte uma carteira diversificada com R$100.000
> Quais os riscos do setor de tecnologia em 2026?
> Me explique o que e P/L e como usar na analise de acoes
```

### Analise Rapida (Linha de Comando)

```bash
# Analise direta de um ticker (retorna JSON)
python -m investment_advisor.main analyze AAPL

# Pergunta direta a IA
python -m investment_advisor.main ask "Vale a pena investir em VALE3?"
```

## Uso como Biblioteca Python

```python
from investment_advisor.market_data import MarketDataProvider
from investment_advisor.fundamental_analysis import FundamentalAnalyzer
from investment_advisor.technical_analysis import TechnicalAnalyzer
from investment_advisor.ai_advisor import AIAdvisor

# Analise fundamentalista
market = MarketDataProvider()
profile = market.get_company_profile("AAPL")

analyzer = FundamentalAnalyzer()
result = analyzer.analyze(profile)
print(f"Score: {result.fundamental_score:.0f}/100")
print(f"Recomendacao: {result.recommendation.value}")

# Analise tecnica
tech = TechnicalAnalyzer()
tech_result = tech.analyze(profile)
print(f"Score Tecnico: {tech_result['score']}/100")

# Chat com IA
advisor = AIAdvisor()
response = advisor.chat("Analise a Apple para mim")
print(response)
```

## Arquitetura

```
investment_advisor/
├── __init__.py               # Package init
├── models.py                 # Modelos de dados (Company, Portfolio, etc.)
├── market_data.py            # Provedor de dados de mercado (yfinance)
├── fundamental_analysis.py   # Motor de analise fundamentalista
├── technical_analysis.py     # Motor de analise tecnica
├── portfolio_manager.py      # Gerenciador de carteira
├── ai_advisor.py             # Assessor IA integrado com Claude
├── cli.py                    # Interface CLI interativa (Rich)
└── main.py                   # Entry point
```

## Dependencias

- `anthropic` - SDK do Claude para integracao com IA
- `yfinance` - Dados de mercado em tempo real
- `pandas` / `numpy` - Processamento de dados e calculos
- `rich` - Interface CLI colorida e interativa

## Aviso Legal

Este framework e uma ferramenta de apoio a decisao. Nao constitui recomendacao de investimento. Sempre faca sua propria analise e consulte um profissional certificado antes de investir.
