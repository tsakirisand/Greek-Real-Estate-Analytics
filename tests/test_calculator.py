from calculator import calculate_investment_metrics

def test_calculate_investment_metrics():
    res = calculate_investment_metrics(
        property_price=200000.0,
        monthly_rent=1000.0,
        down_payment_pct=20.0,
        interest_rate_pct=4.0,
        loan_years=25,
        annual_enfia_tax=400.0,
        annual_maintenance_pct=1.0
    )
    assert res["propertyPrice"] == 200000.0
    assert res["downPayment"] == 40000.0
    assert res["loanAmount"] == 160000.0
    assert res["monthlyMortgage"] > 0
    assert res["grossYieldPct"] == 6.0  # (12000 / 200000) * 100
    assert res["netCapRatePct"] < res["grossYieldPct"]
    assert len(res["amortizationSchedule"]) == 25
    assert res["amortizationSchedule"][-1]["remainingBalance"] == 0.0
