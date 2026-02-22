"""Gerenciador de portfolio."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .market_data import MarketDataProvider
from .models import Portfolio, PortfolioPosition, Sector

logger = logging.getLogger(__name__)

_SECTOR_MAP_REVERSE = {
    "Tecnologia": Sector.TECHNOLOGY,
    "Financas": Sector.FINANCE,
    "Saude": Sector.HEALTHCARE,
    "Energia": Sector.ENERGY,
    "Consumo": Sector.CONSUMER,
    "Industrial": Sector.INDUSTRIAL,
    "Materiais": Sector.MATERIALS,
    "Utilidades": Sector.UTILITIES,
    "Imobiliario": Sector.REAL_ESTATE,
    "Comunicacao": Sector.COMMUNICATION,
}


class PortfolioManager:
    """Gerencia carteira de investimentos com persistencia em arquivo JSON."""

    def __init__(self, data_dir: str = ".investment_advisor"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.market_data = MarketDataProvider()

    def create_portfolio(self, name: str, cash: float = 0.0) -> Portfolio:
        """Cria nova carteira."""
        portfolio = Portfolio(name=name, cash=cash)
        self._save(portfolio)
        return portfolio

    def load_portfolio(self, name: str) -> Portfolio | None:
        """Carrega carteira do disco."""
        filepath = self.data_dir / f"{name}.json"
        if not filepath.exists():
            return None

        data = json.loads(filepath.read_text())
        positions = [
            PortfolioPosition(
                ticker=p["ticker"],
                company_name=p["company_name"],
                shares=p["shares"],
                avg_cost=p["avg_cost"],
                current_price=p.get("current_price", 0),
                sector=_SECTOR_MAP_REVERSE.get(p.get("sector", ""), Sector.OTHER),
            )
            for p in data.get("positions", [])
        ]
        return Portfolio(
            name=data["name"],
            positions=positions,
            cash=data.get("cash", 0),
        )

    def list_portfolios(self) -> list[str]:
        """Lista nomes de carteiras salvas."""
        return [f.stem for f in self.data_dir.glob("*.json")]

    def add_position(
        self,
        portfolio: Portfolio,
        ticker: str,
        shares: float,
        price: float,
    ) -> Portfolio:
        """Adiciona posicao a carteira."""
        try:
            profile = self.market_data.get_company_profile(ticker)
            company_name = profile.name
            sector = profile.sector
            current_price = profile.current_price or price
        except Exception:
            company_name = ticker
            sector = Sector.OTHER
            current_price = price

        position = PortfolioPosition(
            ticker=ticker.upper(),
            company_name=company_name,
            shares=shares,
            avg_cost=price,
            current_price=current_price,
            sector=sector,
        )
        portfolio.add_position(position)
        self._save(portfolio)
        return portfolio

    def remove_position(
        self, portfolio: Portfolio, ticker: str, shares: float | None = None
    ) -> Portfolio:
        """Remove posicao da carteira."""
        portfolio.remove_position(ticker.upper(), shares)
        self._save(portfolio)
        return portfolio

    def update_prices(self, portfolio: Portfolio) -> Portfolio:
        """Atualiza precos atuais de todas as posicoes."""
        for pos in portfolio.positions:
            try:
                profile = self.market_data.get_company_profile(pos.ticker)
                if profile.current_price:
                    pos.current_price = profile.current_price
            except Exception as e:
                logger.warning("Erro ao atualizar preco de %s: %s", pos.ticker, e)
        self._save(portfolio)
        return portfolio

    def get_portfolio_summary(self, portfolio: Portfolio) -> dict:
        """Gera resumo da carteira."""
        positions_data = []
        for pos in portfolio.positions:
            positions_data.append({
                "ticker": pos.ticker,
                "empresa": pos.company_name,
                "setor": pos.sector.value,
                "quantidade": pos.shares,
                "preco_medio": round(pos.avg_cost, 2),
                "preco_atual": round(pos.current_price, 2),
                "valor_investido": round(pos.total_cost, 2),
                "valor_atual": round(pos.current_value, 2),
                "lucro_prejuizo": round(pos.gain_loss, 2),
                "lucro_prejuizo_pct": round(pos.gain_loss_pct, 2),
            })

        return {
            "nome": portfolio.name,
            "caixa": round(portfolio.cash, 2),
            "total_investido": round(portfolio.total_invested, 2),
            "valor_total": round(portfolio.total_value, 2),
            "lucro_prejuizo_total": round(portfolio.total_gain_loss, 2),
            "lucro_prejuizo_total_pct": round(portfolio.total_gain_loss_pct, 2),
            "alocacao_por_setor": portfolio.sector_allocation(),
            "posicoes": positions_data,
            "num_posicoes": len(portfolio.positions),
        }

    def _save(self, portfolio: Portfolio) -> None:
        filepath = self.data_dir / f"{portfolio.name}.json"
        data = {
            "name": portfolio.name,
            "cash": portfolio.cash,
            "positions": [
                {
                    "ticker": p.ticker,
                    "company_name": p.company_name,
                    "shares": p.shares,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "sector": p.sector.value,
                }
                for p in portfolio.positions
            ],
        }
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
