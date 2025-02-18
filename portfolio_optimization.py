import numpy as np
from scipy.optimize import minimize
import risk_management
import logging

# 📌 Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PortfolioOptimization:
    def __init__(self, returns, cov_matrix, risk_free_rate=0.01, max_risk=0.02, scalping_mode=False):
        """
        Inizializza il modulo di ottimizzazione del portafoglio con gestione del rischio adattiva.
        Il bilancio ora viene rilevato dinamicamente, senza bisogno di modificarlo manualmente.
        """
        self.returns = returns
        self.cov_matrix = cov_matrix
        self.risk_free_rate = risk_free_rate
        self.max_risk = max_risk
        self.scalping_mode = scalping_mode
        self.risk_manager = risk_management.RiskManagement(max_risk=self.max_risk)

    def get_dynamic_balance(self, account_data):
        """
        Recupera dinamicamente il saldo disponibile di ogni account.
        """
        return account_data.get("balance", 100)  # Se non trova il saldo, usa 100€ di default

    def optimize_portfolio(self, account_data):
        """
        Ottimizza il portafoglio in base al saldo attuale e alla strategia attiva.
        """
        balance = self.get_dynamic_balance(account_data)

        # ✅ Adatta il rischio in base al saldo rilevato
        max_allowed_risk = self.risk_manager.adjust_risk(balance)

        if self.scalping_mode:
            max_allowed_risk *= 1.5  

        # Funzione obiettivo: massimizzare lo Sharpe Ratio
        def objective(weights):
            port_return = np.dot(weights, self.returns.mean())
            port_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            sharpe_ratio = (port_return - self.risk_free_rate) / port_volatility

            if port_volatility > max_allowed_risk:
                return np.inf  

            return -sharpe_ratio  

        constraints = {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1}
        bounds = [(0, 1) for _ in range(len(self.returns.columns))]
        initial_guess = np.ones(len(self.returns.columns)) / len(self.returns.columns)

        result = minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)

        if result.success:
            logging.info(f"✅ Allocazione ottimale trovata per saldo: {balance}€ → {result.x}")
            return result.x
        else:
            logging.warning("⚠️ Errore nell'ottimizzazione del portafoglio, uso allocazione predefinita.")
            return np.ones(len(self.returns.columns)) / len(self.returns.columns)

# ==============================
# 🔹 ESEMPIO DI UTILIZZO
# ==============================

if __name__ == "__main__":
    simulated_returns = pd.DataFrame(np.random.randn(100, 5) * 0.02, columns=['Asset1', 'Asset2', 'Asset3', 'Asset4', 'Asset5'])
    simulated_cov_matrix = simulated_returns.cov()

    optimizer = PortfolioOptimization(simulated_returns, simulated_cov_matrix, scalping_mode=True)

    account_data = {"balance": 100}  # ✅ Simulazione di un account con 100€ di capitale
    optimized_allocation = optimizer.optimize_portfolio(account_data)
    logging.info(f"✅ Allocazione finale del portafoglio: {optimized_allocation}")