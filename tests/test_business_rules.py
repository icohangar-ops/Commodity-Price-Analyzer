"""
Commodity Price Analyzer — Tests

All contract parameters in this repository are ILLUSTRATIVE EXAMPLES.
Real commercial terms are confidential and must be supplied via private
configuration, never committed here.

Run: python -m pytest tests/ -v
"""
import pytest

from src.contracts.business_rules import (
    calculate_black_mass_payables,
    calculate_primary_offtaker_mhp_offtake,
    calculate_lithium_carbonate_gtc,
    calculate_composite_feedstock,
    convert_usd_mt_to_lb,
    convert_usd_lb_to_mt,
    run_all_calculations,
)


class TestBlackMassPayables:
    def test_basic_calculation(self):
        result = calculate_black_mass_payables(ni_price=18000, co_price=35000)
        assert result["ni_payable_usd_per_mt"] == 14400.0  # 18000 * 0.80
        assert result["co_payable_usd_per_mt"] == 28000.0  # 35000 * 0.80
        assert result["grade_multiplier"] == 0.80

    def test_total_value(self):
        result = calculate_black_mass_payables(ni_price=20000, co_price=40000)
        assert result["total_value_per_mt"] == 48000.0  # (20000 + 40000) * 0.80

    def test_custom_grade_multiplier(self):
        result = calculate_black_mass_payables(
            ni_price=18000, co_price=35000, grade_multiplier=0.90
        )
        assert result["ni_payable_usd_per_mt"] == 16200.0


class TestMHPOfftaker:
    def test_floor_discount(self):
        result = calculate_primary_offtaker_mhp_offtake(ni_price=15000, co_price=30000)
        assert result["floor_ni_usd_per_mt"] == 14250.0  # 15000 * 0.95
        assert result["profit_share_triggered"] is False

    def test_profit_share_triggered(self):
        result = calculate_primary_offtaker_mhp_offtake(ni_price=25000, co_price=30000)
        assert result["profit_share_triggered"] is True
        assert result["incremental_price_above_threshold"] == 7000.0  # 25000 - 18000
        assert result["profit_share_amount"] == 700.0  # 7000 * 0.10

    def test_profit_share_realized_ni(self):
        result = calculate_primary_offtaker_mhp_offtake(ni_price=25000, co_price=30000)
        expected_realized = 23750.0 - 700.0  # floor_ni - profit_share
        assert result["realized_ni_payable"] == expected_realized

    def test_at_threshold(self):
        result = calculate_primary_offtaker_mhp_offtake(ni_price=18000, co_price=30000)
        assert result["profit_share_triggered"] is False


class TestLithiumCarbonateGTC:
    def test_normal_price(self):
        result = calculate_lithium_carbonate_gtc(li_price=22000)
        assert result["effective_price_usd_per_mt"] == 22000
        assert result["floor_protection_active"] is False
        assert result["ceiling_cap_active"] is False

    def test_floor_triggered(self):
        result = calculate_lithium_carbonate_gtc(li_price=15000)
        assert result["floor_protection_active"] is True
        assert result["effective_price_usd_per_mt"] == 18000  # floor

    def test_ceiling_triggered(self):
        result = calculate_lithium_carbonate_gtc(li_price=35000)
        assert result["ceiling_cap_active"] is True
        assert result["effective_price_usd_per_mt"] == 25000  # ceiling


class TestCompositeFeedstock:
    def test_basic_calculation(self):
        result = calculate_composite_feedstock(li_price=25000, ni_price=18000, co_price=32000)
        assert result["li_payable_usd_per_mt"] == round(25000 * 0.90 * 0.70, 2)
        assert result["feedstock_grade"] == 0.90


class TestUnitConversions:
    def test_mt_to_lb(self):
        result = convert_usd_mt_to_lb(2204.62)
        assert result == 1.0

    def test_lb_to_mt(self):
        result = convert_usd_lb_to_mt(1.0)
        assert result == 2204.62


class TestRunAllCalculations:
    def test_full_pipeline(self):
        prices = {"nickel": 18500, "cobalt": 32000, "lithium": 25000}
        results = run_all_calculations(prices)

        assert "contract_calculations" in results
        assert "unit_conversions" in results
        assert "business_insights" in results
        assert "sensitivity_analysis" in results
        assert results["contract_calculations"]["black_mass_payables"]["total_value_per_mt"] > 0

    def test_profit_share_in_insights(self):
        prices = {"nickel": 25000, "cobalt": 32000, "lithium": 25000}
        results = run_all_calculations(prices)
        assert any("TRIGGERED" in str(insight) for insight in results["business_insights"])
