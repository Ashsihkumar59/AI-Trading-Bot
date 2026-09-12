import math

def calculate_position_size(account_balance, entry_price, stop_loss_price, max_risk_pct=0.01):
    """
    Capital aur Stop-Loss ke gap ko mathematically calculate karke 
    exact quantity nikalta hai (Strict 1% risk).
    """
    # 1. Total risk allowed (1% of capital)
    risk_amount = account_balance * max_risk_pct
    
    # 2. Risk per share
    risk_per_share = abs(entry_price - stop_loss_price)
    
    if risk_per_share == 0:
        return 0
        
    # 3. Exact quantity calculation
    raw_quantity = risk_amount / risk_per_share
    final_quantity = math.floor(raw_quantity)
    
    # 4. Maximum affordability check
    max_affordable_qty = math.floor(account_balance / entry_price)
    
    return min(final_quantity, max_affordable_qty)


def check_rrr_gatekeeper(entry_price, stop_loss_price, target_price, min_rrr=2.0):
    """
    Check karta hai ki setup minimum 1:2 Risk-to-Reward de raha hai ya nahi.
    Agar RRR 2.0 ya usse zyada hai toh True dega, warna False.
    """
    # 1. Risk aur Reward calculate karo
    risk = abs(entry_price - stop_loss_price)
    reward = abs(target_price - entry_price)
    
    # Safety Check: Zero division error se bachne ke liye
    if risk == 0:
        return False, 0.0
        
    # 2. RRR Ratio nikalna
    rrr = reward / risk
    
    # 3. Gatekeeper Decision
    if rrr >= min_rrr:
        return True, rrr
    else:
        return False, rrr