def position_size(account_equity, price, per_trade_risk_pct, stop_loss_pct):
    risk_dollars = account_equity * per_trade_risk_pct
    stop_distance = price * stop_loss_pct
    if stop_distance <= 0:
        return 0
    qty = int(risk_dollars / stop_distance)
    return max(qty, 0)

def exceeded_daily_loss(starting_equity, current_equity, max_daily_loss_pct):
    if starting_equity <= 0:
        return False
    drawdown = (starting_equity - current_equity) / starting_equity
    return drawdown >= max_daily_loss_pct
