import json
import os
from io import StringIO
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from fin_agent.config import Config

class PortfolioManager:
    def __init__(self, file_path: str = None):
        if file_path:
            self.file_path = file_path
        else:
            # Default to user config directory (same as .env)
            config_dir = Config.get_config_dir()
            # Ensure directory exists
            os.makedirs(config_dir, exist_ok=True)
            self.file_path = os.path.join(config_dir, "portfolio.json")
            
        self.holdings = self._load_portfolio()

    def _load_portfolio(self) -> Dict:
        if not os.path.exists(self.file_path):
            return {"positions": {}, "cash": 0.0, "history": []}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"positions": {}, "cash": 0.0, "history": []}

    def _save_portfolio(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.holdings, f, ensure_ascii=False, indent=2)

    def add_position(self, ts_code: str, amount: int, price: float):
        """
        Add a position (buy).
        :param ts_code: Stock code
        :param amount: Quantity (positive)
        :param price: Cost per share
        """
        if amount <= 0 or price <= 0:
            return "Error: Amount and price must be positive."

        positions = self.holdings.get("positions", {})
        
        if ts_code in positions:
            # Average cost
            current_amount = positions[ts_code]["amount"]
            current_cost = positions[ts_code]["cost"]
            total_cost = current_amount * current_cost + amount * price
            new_amount = current_amount + amount
            new_cost = total_cost / new_amount
            
            positions[ts_code]["amount"] = new_amount
            positions[ts_code]["cost"] = new_cost
        else:
            positions[ts_code] = {
                "amount": amount,
                "cost": price
            }
        
        # Deduct cash (assuming infinite cash for now if cash is negative, or track simple cash flow)
        # For simple management, we just track cash spent/gained, initially 0
        self.holdings["cash"] = self.holdings.get("cash", 0.0) - (amount * price)
        
        # Log transaction
        self.holdings.setdefault("history", []).append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "BUY",
            "ts_code": ts_code,
            "amount": amount,
            "price": price
        })
        
        self.holdings["positions"] = positions
        self._save_portfolio()
        return f"Successfully added {amount} shares of {ts_code} at {price}."

    def remove_position(self, ts_code: str, amount: int, price: float):
        """
        Remove a position (sell).
        :param ts_code: Stock code
        :param amount: Quantity to sell
        :param price: Sell price
        """
        positions = self.holdings.get("positions", {})
        
        if ts_code not in positions:
            return f"Error: You do not hold {ts_code}."
        
        current_amount = positions[ts_code]["amount"]
        
        if amount > current_amount:
            return f"Error: Insufficient shares. You have {current_amount}, trying to sell {amount}."
            
        # Update position
        if amount == current_amount:
            del positions[ts_code]
        else:
            positions[ts_code]["amount"] = current_amount - amount
            
        # Add cash
        self.holdings["cash"] = self.holdings.get("cash", 0.0) + (amount * price)
        
        # Log transaction
        self.holdings.setdefault("history", []).append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "SELL",
            "ts_code": ts_code,
            "amount": amount,
            "price": price
        })
        
        self.holdings["positions"] = positions
        self._save_portfolio()
        return f"Successfully sold {amount} shares of {ts_code} at {price}."

    def get_portfolio_status(self):
        """
        Get current portfolio status with real-time valuation.
        """
        # Import here to avoid circular dependency
        from fin_agent.tools.tushare_tools import get_realtime_price
        
        positions = self.holdings.get("positions", {})
        if not positions:
            return "Portfolio is empty."
            
        report = []
        total_market_value = 0.0
        total_cost_value = 0.0
        
        for ts_code, data in positions.items():
            amount = data["amount"]
            cost = data["cost"]
            
            # Fetch real-time price
            # get_realtime_price returns a JSON string, we need to parse it
            try:
                price_json = get_realtime_price(ts_code)
                if "Error" in price_json or "No realtime data" in price_json:
                    current_price = cost # Fallback to cost if fails? Or 0? Let's keep cost to avoid panic, but mark it
                    current_price_str = f"{cost} (Est.)"
                else:
                    df = pd.read_json(StringIO(price_json), orient='records')
                    if not df.empty:
                        # Tushare realtime returns 'price', 'bid', 'ask', etc.
                        # Sometimes 'price' is the current price.
                        current_price = float(df.iloc[0]['price'])
                        current_price_str = str(current_price)
                    else:
                        current_price = cost
                        current_price_str = f"{cost} (Est.)"
            except:
                current_price = cost
                current_price_str = f"{cost} (Est.)"
                
            market_value = amount * current_price
            cost_value = amount * cost
            pnl = market_value - cost_value
            pnl_pct = (pnl / cost_value) * 100 if cost_value != 0 else 0
            
            total_market_value += market_value
            total_cost_value += cost_value
            
            report.append({
                "ts_code": ts_code,
                "amount": amount,
                "cost": cost,
                "current_price": current_price,
                "market_value": market_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct
            })
            
        total_pnl = total_market_value - total_cost_value
        total_pnl_pct = (total_pnl / total_cost_value) * 100 if total_cost_value != 0 else 0
        
        summary = {
            "positions": report,
            "total_market_value": total_market_value,
            "total_cost_value": total_cost_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "cash": self.holdings.get("cash", 0.0)
        }
        
        return summary

    def clear_portfolio(self):
        self.holdings = {"positions": {}, "cash": 0.0, "history": []}
        self._save_portfolio()
        return "Portfolio cleared."
