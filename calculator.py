import math

def calculate_investment_metrics(
    property_price: float = 200000.0,
    monthly_rent: float = 900.0,
    down_payment_pct: float = 25.0,
    interest_rate_pct: float = 3.8,
    loan_years: int = 25,
    annual_enfia_tax: float = 450.0,
    annual_maintenance_pct: float = 1.0
) -> dict:
    """
    Calculates real estate financial investment metrics, including Gross Yield,
    Net Cap Rate, ENFIA tax friction, monthly mortgage payment (PMT),
    net monthly cash flow, and Cash-on-Cash Return.
    """
    down_payment = property_price * (down_payment_pct / 100.0)
    loan_amount = max(0.0, property_price - down_payment)
    
    # PMT Monthly Mortgage Calculation
    r = (interest_rate_pct / 100.0) / 12.0
    n = loan_years * 12
    
    if r > 0 and n > 0 and loan_amount > 0:
        monthly_mortgage = loan_amount * (r * (1 + r)**n) / (((1 + r)**n) - 1)
    else:
        monthly_mortgage = 0.0
        
    annual_mortgage = monthly_mortgage * 12.0
    total_repayment = monthly_mortgage * n
    total_interest = total_repayment - loan_amount if loan_amount > 0 else 0.0
    
    gross_annual_rent = monthly_rent * 12.0
    gross_yield = (gross_annual_rent / property_price) * 100.0 if property_price > 0 else 0.0
    
    annual_maintenance = property_price * (annual_maintenance_pct / 100.0)
    total_annual_expenses = annual_enfia_tax + annual_maintenance
    
    net_operating_income = gross_annual_rent - total_annual_expenses
    cap_rate = (net_operating_income / property_price) * 100.0 if property_price > 0 else 0.0
    
    net_annual_cash_flow = net_operating_income - annual_mortgage
    net_monthly_cash_flow = net_annual_cash_flow / 12.0
    
    cash_on_cash = (net_annual_cash_flow / down_payment) * 100.0 if down_payment > 0 else 0.0

    # Build Amortization Schedule per year
    amortization_schedule = []
    remaining_balance = loan_amount
    cumulative_interest = 0.0
    
    for y in range(1, loan_years + 1):
        year_interest = 0.0
        year_principal = 0.0
        for _ in range(12):
            if remaining_balance <= 0:
                break
            m_interest = remaining_balance * r
            m_principal = min(remaining_balance, monthly_mortgage - m_interest)
            year_interest += m_interest
            year_principal += m_principal
            remaining_balance -= m_principal
            
        cumulative_interest += year_interest
        amortization_schedule.append({
            "year": y,
            "principalPaid": round(year_principal, 2),
            "interestPaid": round(year_interest, 2),
            "cumulativeInterest": round(cumulative_interest, 2),
            "remainingBalance": round(max(0.0, remaining_balance), 2)
        })

    return {
        "propertyPrice": round(property_price, 2),
        "downPayment": round(down_payment, 2),
        "loanAmount": round(loan_amount, 2),
        "monthlyMortgage": round(monthly_mortgage, 2),
        "totalInterest": round(total_interest, 2),
        "grossYieldPct": round(gross_yield, 2),
        "netCapRatePct": round(cap_rate, 2),
        "netMonthlyCashFlow": round(net_monthly_cash_flow, 2),
        "cashOnCashPct": round(cash_on_cash, 2),
        "annualEnfia": round(annual_enfia_tax, 2),
        "annualMaintenance": round(annual_maintenance, 2),
        "amortizationSchedule": amortization_schedule
    }
