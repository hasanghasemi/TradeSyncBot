import MetaTrader5 as mt5
import time
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

FILE_PATH = "accounts.json"

# --- Paths to the two MetaTrader terminals ---
# Master account (C drive)
MASTER_PATH = r"C:\Program Files\LiteFinance MT5 Terminal\terminal64.exe" 
# Slave account (E drive)
SLAVE_PATH = r"E:\Program Files\LiteFinance MT5 Terminal\terminal64.exe"  
# --------------------------------------------

if not os.path.exists(FILE_PATH):
    logging.error(f"{FILE_PATH} not found! Please create it with your account credentials.")
    exit()

with open(FILE_PATH, 'r') as json_file:
    data = json.load(json_file)

MASTER_ACCOUNT = data["account_1"]
SLAVE_ACCOUNT = data["account_2"]

def login_to_account(account, terminal_path, terminal_name):
    """
    Connect to a specific terminal and login to the account.
    """
    mt5.shutdown()
    time.sleep(2) 
    
    if not mt5.initialize(path=terminal_path):
        logging.error(f"Failed to initialize {terminal_name} MT5 at {terminal_path}: {mt5.last_error()}")
        return False
    
    account_info = mt5.account_info()
    if account_info is not None:
        if account_info.login == int(account['login']):
            logging.info(f"Already logged into {terminal_name} account {account['login']}.")
            time.sleep(2)
            return True
    
    authorized = mt5.login(
        login=int(account['login']), 
        password=account['password'], 
        server=account['server']
    )
    
    if not authorized:
        logging.error(f"Failed to login to {terminal_name} account {account['login']}: {mt5.last_error()}")
        return False
        
    logging.info(f"Logged into {terminal_name} account {account['login']}.")
    time.sleep(3)
    return True

def find_matching_symbol(master_symbol):
    """
    Try to find the corresponding symbol on the slave account.
    Handles common suffixes like _i, .r, micro, etc.
    """
    if mt5.symbol_select(master_symbol, True):
        return master_symbol
    suffixes = ["_i", ".r", "micro", "pro", ".a", ""]
    for suffix in suffixes:
        test_symbol = master_symbol + suffix
        if mt5.symbol_select(test_symbol, True):
            logging.info(f"Matching symbol found on slave account: {test_symbol}")
            return test_symbol
    return None

def send_order_with_retry(request):
    """
    Try different filling modes to overcome the 10030 error.
    """
    request['type_filling'] = mt5.ORDER_FILLING_FOK
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        return result
        
    if result.retcode == 10030:
        logging.warning("FOK filling mode unsupported. Trying IOC...")
        request['type_filling'] = mt5.ORDER_FILLING_IOC
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return result
            
        if result.retcode == 10030:
            logging.warning("IOC filling mode unsupported. Trying RETURN...")
            request['type_filling'] = mt5.ORDER_FILLING_RETURN
            result = mt5.order_send(request)
            
    return result

def monitor_trades():
    if not login_to_account(MASTER_ACCOUNT, MASTER_PATH, "MASTER"):
        return

    monitored_trades = {trade.ticket: trade for trade in mt5.positions_get() or []}
    copied_trades = {}

    while True:
        current_trades = mt5.positions_get() or []
        current_trades_dict = {trade.ticket: trade for trade in current_trades}

        # 1. Detect new trades on Master account
        new_tickets = set(current_trades_dict.keys()) - set(monitored_trades.keys())
        for ticket in new_tickets:
            trade = current_trades_dict[ticket]
            logging.info(f"New trade detected on MASTER: {trade}")
            
            if not login_to_account(SLAVE_ACCOUNT, SLAVE_PATH, "SLAVE"):
                return
            slave_ticket = copy_trade(trade)
            
            if not login_to_account(MASTER_ACCOUNT, MASTER_PATH, "MASTER"):
                return
            
            if slave_ticket:
                copied_trades[ticket] = trade
                logging.info(f"Tracking Master Ticket {ticket} <-> Slave Ticket {slave_ticket}")

        # 2. Detect closed trades on Master account
        closed_tickets = set(monitored_trades.keys()) - set(current_trades_dict.keys())
        for ticket in closed_tickets:
            if ticket in copied_trades:
                if not login_to_account(SLAVE_ACCOUNT, SLAVE_PATH, "SLAVE"):
                    return
                
                if close_trade(copied_trades[ticket]):
                    del copied_trades[ticket]
                else:
                    logging.warning(f"Failed to close trade on SLAVE. Will retry. Master Ticket: {ticket}")
                
                if not login_to_account(MASTER_ACCOUNT, MASTER_PATH, "MASTER"):
                    return

        # 3. Detect SL/TP changes on Master account
        for ticket, trade in current_trades_dict.items():
            if ticket in monitored_trades:
                prev_trade = monitored_trades[ticket]
                if trade.sl != prev_trade.sl or trade.tp != prev_trade.tp:
                    logging.info(f"Trade modified (SL/TP changed) on MASTER: {trade}")
                    if not login_to_account(SLAVE_ACCOUNT, SLAVE_PATH, "SLAVE"):
                        return
                    update_position_on_slave(trade)
                    if not login_to_account(MASTER_ACCOUNT, MASTER_PATH, "MASTER"):
                        return

        monitored_trades = current_trades_dict
        time.sleep(2)

def copy_trade(trade):
    try:
        master_symbol = trade.symbol
        symbol = find_matching_symbol(master_symbol)
        
        if not symbol:
            logging.error(f"Could not find matching symbol for '{master_symbol}' on SLAVE.")
            return None

        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logging.error(f"Failed to get symbol info for {symbol}.")
            return None

        original_volume = trade.volume
        rounded_lot_size = round(original_volume / symbol_info.volume_step) * symbol_info.volume_step
        if rounded_lot_size < symbol_info.volume_min:
            rounded_lot_size = symbol_info.volume_min

        slave_account_info = mt5.account_info()
        if not slave_account_info:
            logging.error(f"Failed to get SLAVE account info: {mt5.last_error()}")
            return None

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logging.error(f"Failed to get tick info for {symbol}.")
            return None
        price = tick.ask if trade.type == mt5.ORDER_TYPE_BUY else tick.bid

        margin_required = price * rounded_lot_size * symbol_info.margin_initial
        if margin_required > slave_account_info.margin_free:
            logging.error(f"Not enough margin on SLAVE. Required: {margin_required:.2f}, Free: {slave_account_info.margin_free:.2f}")
            return None

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': rounded_lot_size,
            'type': mt5.ORDER_TYPE_BUY if trade.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_SELL,
            'price': price,
            'sl': trade.sl,
            'tp': trade.tp,
            'deviation': 20,
            'magic': trade.ticket,
            'comment': 'Copied trade',
            'type_time': mt5.ORDER_TIME_GTC,
        }

        logging.info(f"Sending trade request to SLAVE (Magic: {trade.ticket}): {request}")
        result = send_order_with_retry(request)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"Trade copied successfully to SLAVE. Master Ticket: {trade.ticket}, Slave Ticket: {result.order}")
            return result.order
        else:
            logging.error(f"Failed to copy trade to SLAVE. Retcode: {result.retcode}, Result: {result}")
            return None

    except Exception as e:
        logging.error(f"Error copying trade: {e}")
        return None

def update_position_on_slave(master_trade):
    try:
        symbol = find_matching_symbol(master_trade.symbol)
        if not symbol: return

        slave_positions = mt5.positions_get(symbol=symbol)
        if not slave_positions: return

        slave_position = None
        for pos in slave_positions:
            if pos.magic == master_trade.ticket:
                slave_position = pos
                break
                
        if not slave_position:
            logging.error(f"Could not find slave position with Magic {master_trade.ticket} to update.")
            return

        if slave_position.sl == master_trade.sl and slave_position.tp == master_trade.tp:
            return

        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': symbol,
            'position': slave_position.ticket,
            'sl': master_trade.sl,
            'tp': master_trade.tp,
        }
        logging.info(f"Sending SL/TP update to SLAVE (Magic: {master_trade.ticket}): {request}")
        mt5.order_send(request)
    except Exception as e:
        logging.error(f"Error updating position: {e}")

def close_trade(trade):
    try:
        symbol = find_matching_symbol(trade.symbol)
        if not symbol: return False

        close_type = mt5.ORDER_TYPE_SELL if trade.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        
        positions = mt5.positions_get(symbol=symbol)
        if not positions: 
            return True 

        position_to_close = None
        for pos in positions:
            if pos.magic == trade.ticket:
                position_to_close = pos
                break
                
        if not position_to_close:
            logging.error(f"Could not find slave position with Magic {trade.ticket} to close.")
            return True 

        tick = mt5.symbol_info_tick(symbol)
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'position': position_to_close.ticket,
            'symbol': symbol,
            'volume': position_to_close.volume,
            'type': close_type,
            'price': price,
            'deviation': 20,
            'magic': trade.ticket,
            'comment': 'Close copied trade',
            'type_time': mt5.ORDER_TIME_GTC,
        }
        logging.info(f"Sending close request to SLAVE (Magic: {trade.ticket}): {request}")
        result = send_order_with_retry(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"Trade closed successfully on SLAVE. Magic: {trade.ticket}")
            return True
        else:
            logging.error(f"Failed to close trade on SLAVE. Magic: {trade.ticket}, Retcode: {result.retcode}")
            return False 
    except Exception as e:
        logging.error(f"Error closing trade: {e}")
        return False

if __name__ == "__main__":
    try:
        print("--- TradeSyncBot Setup ---")
        print(f"Master Terminal: {MASTER_PATH}")
        print(f"Slave Terminal: {SLAVE_PATH}")
        
        if not login_to_account(SLAVE_ACCOUNT, SLAVE_PATH, "SLAVE"):
            print("Could not connect to SLAVE terminal. Please check path and credentials.")
            exit()
        
        input("Please make sure Algo Trading is enabled in BOTH MetaTrader terminals. Press Enter to continue...")

        monitor_trades()

    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
    finally:
        mt5.shutdown()