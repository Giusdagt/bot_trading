import data_handler  # Per monitorare i dati di mercato
import logging

# 📌 Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RiskManagement:
    def __init__(self, max_risk=0.02, max_drawdown=0.1, trailing_stop_pct=0.03, initial_balance=100, scalping_mode=False):
        """
        Modulo di gestione del rischio per scalping e swing trading.
        """
        self.max_risk = max_risk
        self.max_drawdown = max_drawdown
        self.trailing_stop_pct = trailing_stop_pct
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.max_balance = initial_balance
        self.min_balance = initial_balance
        self.scalping_mode = scalping_mode  # ✅ Modalità scalping attivabile

    def set_max_risk(self, new_max_risk):
        """Imposta un nuovo livello di rischio massimo"""
        self.max_risk = new_max_risk
        logging.info(f"✅ Rischio massimo aggiornato a: {self.max_risk}")

    def calculate_position_size(self, current_balance, stop_loss):
        """
        Calcola la dimensione della posizione in base al rischio massimo e allo stop loss.
        """
        risk_amount = current_balance * self.max_risk
        position_size = risk_amount / stop_loss

        # ✅ Se scalping attivo, riduci la dimensione delle posizioni per gestire il rischio
        if self.scalping_mode:
            position_size *= 0.7  

        return position_size

    def dynamic_stop_loss(self, entry_price, predicted_price, stop_loss):
        """
        Aggiorna lo stop loss dinamicamente in base all'andamento del prezzo.
        """
        if predicted_price > entry_price:
            new_stop_loss = entry_price * (1 - self.trailing_stop_pct)
        else:
            new_stop_loss = entry_price * (1 + self.trailing_stop_pct)

        return new_stop_loss

    def trailing_stop(self, entry_price, predicted_price):
        """
        Calcola il trailing stop in base alla previsione del prezzo.
        """
        if predicted_price > entry_price:
            trailing_stop_price = entry_price * (1 + self.trailing_stop_pct)
        else:
            trailing_stop_price = entry_price * (1 - self.trailing_stop_pct)

        return trailing_stop_price

    def adjust_risk_based_on_performance(self, current_balance):
        """
        Adatta il rischio in base alla performance attuale del saldo.
        """
        performance_factor = (current_balance - self.initial_balance) / self.initial_balance
        adjusted_risk = self.max_risk + (performance_factor * 0.1)  

        # ✅ Limita il rischio massimo e minimo
        adjusted_risk = max(min(adjusted_risk, 0.05), 0.02)

        logging.info(f"📊 Rischio adattato dinamicamente a: {adjusted_risk}")
        return adjusted_risk

    def check_drawdown(self, current_balance):
        """
        Verifica se il drawdown ha superato il limite e blocca il trading se necessario.
        """
        if current_balance < self.min_balance:
            self.min_balance = current_balance

        drawdown = (self.max_balance - current_balance) / self.max_balance
        if drawdown > self.max_drawdown:
            logging.warning(f"⚠️ Drawdown superiore al limite ({drawdown * 100:.2f}% > {self.max_drawdown * 100:.2f}%) - Blocco del trading.")
            return True
        return False

class TradingBot:
    def __init__(self, account_name, risk_management):
        self.account_name = account_name
        self.risk_management = risk_management
        self.current_position = None
        self.entry_price = None

    def open_trade(self, market_data, stop_loss, take_profit):
        """
        Apre una posizione di trading gestendo il rischio dinamicamente.
        """
        position_size = self.risk_management.calculate_position_size(self.risk_management.current_balance, stop_loss)
        logging.info(f"📈 {self.account_name} → Apertura posizione di {position_size:.4f} unità.")

        self.current_position = 'long'  
        self.entry_price = market_data['price']

    def manage_trade(self, market_data):
        """
        Aggiorna lo stop loss e gestisce il trade in base al mercato.
        """
        if self.current_position == 'long':
            trailing_stop = self.risk_management.trailing_stop(self.entry_price, market_data['predicted_price'])
            logging.info(f"🔄 {self.account_name} → Stop loss aggiornato a: {trailing_stop:.2f}")

    def close_trade(self):
        """
        Chiude la posizione di trading.
        """
        logging.info(f"❌ {self.account_name} → Chiusura posizione.")
        self.current_position = None
        self.entry_price = None

# ✅ Creazione degli oggetti di gestione del rischio per ogni account
denny_risk_management = RiskManagement(initial_balance=100, scalping_mode=True)
giuseppe_risk_management = RiskManagement(initial_balance=100, scalping_mode=False)

# ✅ Creazione dei bot di trading per Denny e Giuseppe
denny_bot = TradingBot(account_name="Denny", risk_management=denny_risk_management)
giuseppe_bot = TradingBot(account_name="Giuseppe", risk_management=giuseppe_risk_management)

# ✅ Simulazione di apertura di un trade per entrambi i bot
market_data = {'price': 100, 'predicted_price': 105}
denny_bot.open_trade(market_data, stop_loss=5, take_profit=10)
giuseppe_bot.open_trade(market_data, stop_loss=5, take_profit=10)

# ✅ Gestione del trade (aggiornamento dello stop loss)
market_data = {'price': 102, 'predicted_price': 107}
denny_bot.manage_trade(market_data)
giuseppe_bot.manage_trade(market_data)

# ✅ Chiusura dei trade
denny_bot.close_trade()
giuseppe_bot.close_trade()