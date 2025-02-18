import gym
from gym import spaces
import numpy as np
import pandas as pd
import data_handler
from risk_management import RiskManagement
import indicators
import drl_agent
import logging
import os
import json
import requests

# 📌 Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Percorsi per backup delle performance del bot
BACKUP_DIR = "/mnt/usb_trading_data/trading_performance" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

CLOUD_BACKTEST_URL = "https://your-cloud-backtesting.com/run"  # Esempio di API cloud

class TradingEnv(gym.Env):
    """
    Ambiente di trading AI con supporto per più account.
    """
    def __init__(self, data: pd.DataFrame, initial_balances={"Danny": 1000, "Giuseppe": 1000}):
        super(TradingEnv, self).__init__()
        self.data = data_handler.load_normalized_data(data)
        self.current_step = 0
        self.accounts = {account: {"balance": initial_balances[account], "shares_held": 0, "net_worth": initial_balances[account]} for account in initial_balances}
        self.max_steps = len(self.data)

        # Spazio delle azioni: [0 = Sell, 1 = Hold, 2 = Buy]
        self.action_space = spaces.Discrete(3)

        # Spazio delle osservazioni: Dati di mercato + indicatori
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(self.data.shape[1] + len(indicators.get_indicators_list()),), dtype=np.float32
        )

        # Moduli di gestione del rischio per ogni account
        self.risk_management = {account: RiskManagement(self.accounts[account]["balance"], account) for account in self.accounts}

        # AI Trading Agent (DRL) per ogni account
        self.drl_agents = {account: drl_agent.DRLAgent(model_type='PPO', data=self.data) for account in self.accounts}

    def reset(self):
        """Resetta l'ambiente e registra lo stato iniziale per il backtesting."""
        self.current_step = 0
        for account in self.accounts:
            self.accounts[account]["balance"] = self.accounts[account]["net_worth"]
            self.accounts[account]["shares_held"] = 0
        self.log_performance("RESET")
        return self._get_observation()

    def step(self, actions):
        """Esegue un'azione nel mercato per ogni account e registra i dati di performance."""
        for account, action in actions.items():
            self._take_action(account, action)
        self.current_step += 1
        done = self.current_step >= self.max_steps - 1
        rewards = {account: self.accounts[account]["net_worth"] - self.accounts[account]["balance"] for account in self.accounts}
        self.log_performance(actions)
        return self._get_observation(), rewards, done, {}

    def _take_action(self, account, action):
        """Esegue un'azione di trading per un account con gestione del rischio e delle commissioni."""
        current_price = self.data.iloc[self.current_step]['close']
        risk_limit = self.risk_management[account].get_risk_level()
        trading_fee = 0.001  # 0.1% commissione di trading

        if action == 0:  # SELL
            if self.accounts[account]["shares_held"] > 0:
                self.accounts[account]["balance"] += (self.accounts[account]["shares_held"] * current_price) * (1 - trading_fee)
                self.accounts[account]["shares_held"] = 0

        elif action == 2:  # BUY
            if self.accounts[account]["balance"] > 0:
                allowed_balance = self.risk_management[account].get_max_investment(self.accounts[account]["balance"])
                invest_amount = min(allowed_balance, risk_limit)
                self.accounts[account]["shares_held"] += (invest_amount / current_price) * (1 - trading_fee)
                self.accounts[account]["balance"] -= invest_amount

        # Aggiorna il net worth
        self.accounts[account]["net_worth"] = self.accounts[account]["balance"] + (self.accounts[account]["shares_held"] * current_price)

    def _get_observation(self):
        """Ottiene i dati di mercato e indicatori per l'AI."""
        market_data = self.data.iloc[self.current_step].values
        indicators_data = indicators.calculate_indicators(self.data.iloc[:self.current_step + 1])
        return np.concatenate((market_data, indicators_data))

    def render(self):
        """Visualizza lo stato attuale del bot e registra le performance."""
        for account in self.accounts:
            logging.info(
                f"📊 {account} → Step: {self.current_step}, Net Worth: {self.accounts[account]['net_worth']:.2f}, "
                f"Balance: {self.accounts[account]['balance']:.2f}, Shares Held: {self.accounts[account]['shares_held']:.2f}"
            )

    def log_performance(self, actions):
        """Registra le operazioni di trading e il net worth nel tempo per ogni account."""
        performance_data = {
            "timestamp": self.current_step,
            "accounts": {account: {"balance": self.accounts[account]["balance"], "net_worth": self.accounts[account]["net_worth"], "shares_held": self.accounts[account]["shares_held"], "action": actions[account]} for account in self.accounts}
        }
        backup_file = os.path.join(BACKUP_DIR, "trading_performance.json")

        try:
            if os.path.exists(backup_file):
                with open(backup_file, "r") as file:
                    data = json.load(file)
            else:
                data = []

            data.append(performance_data)

            with open(backup_file, "w") as file:
                json.dump(data, file, indent=4)
            logging.info("✅ Performance trading registrata con successo per entrambi gli account.")
        except Exception as e:
            logging.error(f"⚠️ Errore nel salvataggio delle performance di trading: {e}")

# ==============================
# 🔹 ESEMPIO DI UTILIZZO
# ==============================

if __name__ == "__main__":
    try:
        logging.info("📥 Caricamento dati elaborati...")
        data = data_handler.load_normalized_data()
        env = TradingEnv(data=data, initial_balances={"Danny": 1000, "Giuseppe": 1000})
        observation = env.reset()

        for step in range(10):
            actions = {account: env.action_space.sample() for account in env.accounts}
            observation, rewards, done, _ = env.step(actions)
            if done:
                break

        env.render()

    except Exception as e:
        logging.error(f"❌ Errore nell'esecuzione dell'ambiente di trading: {e}")
