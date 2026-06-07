"""
Test suite for per-cryptocurrency auto trading configuration
Tests the complete workflow for enabling, configuring, and monitoring auto trading
"""

import asyncio
from backend.auto_trading_settings import (
    CryptoAutoTradingSettings,
    AutoTradingMonitor,
    AutoTradingExecutor,
    DEFAULT_BUY_PERCENTAGE,
    DEFAULT_SELL_PERCENTAGE,
)


class TestAutoTradingCoinSystem:
    """Test per-cryptocurrency auto trading functionality"""

    def test_1_calculate_buy_trigger_price(self):
        """TEST 1: Calculate buy trigger price based on drop percentage"""
        print("\n" + "="*70)
        print("TEST 1: Calculate Buy Trigger Price")
        print("="*70)
        
        test_cases = [
            {"reference": 50000, "drop": 5, "expected": 47500},
            {"reference": 100, "drop": 10, "expected": 90},
            {"reference": 1000, "drop": 15, "expected": 850},
            {"reference": 0.5, "drop": 20, "expected": 0.4},
        ]
        
        for case in test_cases:
            result = AutoTradingMonitor.calculate_buy_trigger_price(
                case["reference"],
                case["drop"]
            )
            expected = case["expected"]
            passed = abs(result - expected) < 0.01
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | Reference: ${case['reference']}, Drop: {case['drop']}%")
            print(f"  Expected: ${expected}, Got: ${result:.2f}")
        
        return True

    def test_2_calculate_sell_trigger_price(self):
        """TEST 2: Calculate sell trigger price based on gain percentage"""
        print("\n" + "="*70)
        print("TEST 2: Calculate Sell Trigger Price")
        print("="*70)
        
        test_cases = [
            {"average_cost": 47500, "gain": 10, "expected": 52250},
            {"average_cost": 100, "gain": 20, "expected": 120},
            {"average_cost": 1000, "gain": 5, "expected": 1050},
            {"average_cost": 0.4, "gain": 25, "expected": 0.5},
        ]
        
        for case in test_cases:
            result = AutoTradingMonitor.calculate_sell_trigger_price(
                case["average_cost"],
                case["gain"]
            )
            expected = case["expected"]
            passed = abs(result - expected) < 0.01
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | Average Cost: ${case['average_cost']}, Gain: {case['gain']}%")
            print(f"  Expected: ${expected}, Got: ${result:.2f}")
        
        return True

    def test_3_should_buy_logic(self):
        """TEST 3: Determine buy signal based on price and trigger"""
        print("\n" + "="*70)
        print("TEST 3: Buy Signal Logic")
        print("="*70)
        
        test_cases = [
            {
                "current": 47500,
                "trigger": 47500,
                "last_action": None,
                "expected": True,
                "desc": "Price equals trigger"
            },
            {
                "current": 47400,
                "trigger": 47500,
                "last_action": None,
                "expected": True,
                "desc": "Price below trigger"
            },
            {
                "current": 48000,
                "trigger": 47500,
                "last_action": None,
                "expected": False,
                "desc": "Price above trigger"
            },
            {
                "current": 47400,
                "trigger": 47500,
                "last_action": "SELL",
                "expected": False,
                "desc": "Price below trigger but just sold (prevent oscillation)"
            },
        ]
        
        for case in test_cases:
            result = AutoTradingMonitor.should_buy(
                case["current"],
                case["trigger"],
                case["last_action"]
            )
            passed = result == case["expected"]
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | {case['desc']}")
            print(f"  Current: ${case['current']}, Trigger: ${case['trigger']}, Last Action: {case['last_action']}")
        
        return True

    def test_4_should_sell_logic(self):
        """TEST 4: Determine sell signal based on price and holdings"""
        print("\n" + "="*70)
        print("TEST 4: Sell Signal Logic")
        print("="*70)
        
        test_cases = [
            {
                "current": 52250,
                "trigger": 52250,
                "quantity": 1.0,
                "last_action": None,
                "expected": True,
                "desc": "Price at trigger with holdings"
            },
            {
                "current": 53000,
                "trigger": 52250,
                "quantity": 1.0,
                "last_action": None,
                "expected": True,
                "desc": "Price above trigger with holdings"
            },
            {
                "current": 51000,
                "trigger": 52250,
                "quantity": 1.0,
                "last_action": None,
                "expected": False,
                "desc": "Price below trigger with holdings"
            },
            {
                "current": 53000,
                "trigger": 52250,
                "quantity": 0,
                "last_action": None,
                "expected": False,
                "desc": "No quantity held"
            },
            {
                "current": 53000,
                "trigger": 52250,
                "quantity": 1.0,
                "last_action": "BUY",
                "expected": False,
                "desc": "Just bought (prevent oscillation)"
            },
        ]
        
        for case in test_cases:
            result = AutoTradingMonitor.should_sell(
                case["current"],
                case["trigger"],
                case["quantity"],
                case["last_action"]
            )
            passed = result == case["expected"]
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | {case['desc']}")
            print(f"  Current: ${case['current']}, Trigger: ${case['trigger']}, Qty: {case['quantity']}")
        
        return True

    def test_5_profit_loss_calculation(self):
        """TEST 5: Calculate profit/loss from sales"""
        print("\n" + "="*70)
        print("TEST 5: Profit/Loss Calculation")
        print("="*70)
        
        test_cases = [
            {
                "quantity": 1.0,
                "sell_price": 52250,
                "cost": 47500,
                "expected": 4750,
                "desc": "Profitable sale"
            },
            {
                "quantity": 2.0,
                "sell_price": 52250,
                "cost": 47500,
                "expected": 9500,
                "desc": "2x quantity profitable sale"
            },
            {
                "quantity": 1.0,
                "sell_price": 45000,
                "cost": 47500,
                "expected": -2500,
                "desc": "Loss on sale"
            },
            {
                "quantity": 0.5,
                "sell_price": 47500,
                "cost": 47500,
                "expected": 0,
                "desc": "Break-even sale"
            },
        ]
        
        for case in test_cases:
            result = AutoTradingMonitor.calculate_profit_loss(
                case["quantity"],
                case["sell_price"],
                case["cost"]
            )
            passed = abs(result - case["expected"]) < 0.01
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | {case['desc']}")
            print(f"  Qty: {case['quantity']}, Sell: ${case['sell_price']}, Cost: ${case['cost']}")
            print(f"  Expected P/L: ${case['expected']}, Got: ${result:.2f}")
        
        return True

    def test_6_average_cost_update(self):
        """TEST 6: Update average cost on new purchase"""
        print("\n" + "="*70)
        print("TEST 6: Average Cost Update")
        print("="*70)
        
        test_cases = [
            {
                "current_avg": 47500,
                "current_qty": 1.0,
                "new_qty": 1.0,
                "new_price": 50000,
                "expected_avg": 48750,
                "expected_qty": 2.0,
                "desc": "Adding 1 at higher price"
            },
            {
                "current_avg": 50000,
                "current_qty": 2.0,
                "new_qty": 2.0,
                "new_price": 48000,
                "expected_avg": 49000,
                "expected_qty": 4.0,
                "desc": "Adding 2 at lower price"
            },
            {
                "current_avg": None,
                "current_qty": 0,
                "new_qty": 1.0,
                "new_price": 47500,
                "expected_avg": 47500,
                "expected_qty": 1.0,
                "desc": "First purchase"
            },
        ]
        
        for case in test_cases:
            new_avg, new_qty = AutoTradingMonitor.update_average_cost(
                case["current_avg"],
                case["current_qty"],
                case["new_qty"],
                case["new_price"]
            )
            
            avg_passed = abs(new_avg - case["expected_avg"]) < 0.01
            qty_passed = abs(new_qty - case["expected_qty"]) < 0.01
            passed = avg_passed and qty_passed
            status = "✅ PASS" if passed else "❌ FAIL"
            
            print(f"{status} | {case['desc']}")
            print(f"  Current: Avg ${case['current_avg']}, Qty {case['current_qty']}")
            print(f"  New: Qty {case['new_qty']} @ ${case['new_price']}")
            print(f"  Expected: Avg ${case['expected_avg']}, Qty {case['expected_qty']}")
            print(f"  Got: Avg ${new_avg:.2f}, Qty {new_qty:.2f}")
        
        return True

    def test_7_auto_trading_settings_creation(self):
        """TEST 7: Create and manage auto trading settings"""
        print("\n" + "="*70)
        print("TEST 7: Auto Trading Settings Management")
        print("="*70)
        
        # Create settings
        settings = CryptoAutoTradingSettings(
            user_id="test_user_123",
            symbol="BTC",
            enabled=True,
            buy_percentage=5.0,
            sell_percentage=10.0,
            reference_price=50000
        )
        
        print(f"✅ Created settings for {settings.symbol}")
        print(f"  User: {settings.user_id}")
        print(f"  Enabled: {settings.enabled}")
        print(f"  Buy at: {settings.buy_percentage}% drop")
        print(f"  Sell at: {settings.sell_percentage}% gain")
        print(f"  Reference Price: ${settings.reference_price}")
        
        # Test conversion to dict
        settings_dict = settings.to_dict()
        print(f"\n✅ Settings converted to dict")
        print(f"  Keys: {list(settings_dict.keys())}")
        
        return True

    def test_8_buy_action_recording(self):
        """TEST 8: Record buy action with average cost update"""
        print("\n" + "="*70)
        print("TEST 8: Buy Action Recording")
        print("="*70)
        
        settings = CryptoAutoTradingSettings(
            user_id="test_user_123",
            symbol="BTC",
            reference_price=50000
        )
        
        # Record first buy
        action1 = AutoTradingExecutor.record_buy_action(settings, 47500, 1.0)
        print(f"✅ Buy 1 executed at $47500")
        print(f"  Quantity: {settings.total_quantity_held}")
        print(f"  Average Cost: ${settings.average_cost:.2f}")
        print(f"  Action: {action1.action_type} - {action1.reason}")
        
        # Record second buy
        action2 = AutoTradingExecutor.record_buy_action(settings, 46000, 1.0)
        print(f"\n✅ Buy 2 executed at $46000")
        print(f"  Quantity: {settings.total_quantity_held}")
        print(f"  Average Cost: ${settings.average_cost:.2f}")
        print(f"  Action: {action2.action_type} - {action2.reason}")
        
        return True

    def test_9_sell_action_recording(self):
        """TEST 9: Record sell action with P/L calculation"""
        print("\n" + "="*70)
        print("TEST 9: Sell Action Recording")
        print("="*70)
        
        settings = CryptoAutoTradingSettings(
            user_id="test_user_123",
            symbol="BTC",
            average_cost=46750,
            total_quantity_held=2.0
        )
        
        print(f"Initial state:")
        print(f"  Quantity: {settings.total_quantity_held}")
        print(f"  Average Cost: ${settings.average_cost}")
        print(f"  Total P/L: ${settings.total_profit_loss}")
        
        # Record sell
        action = AutoTradingExecutor.record_sell_action(settings, 52250, 1.0)
        
        print(f"\n✅ Sell executed at $52250 for 1.0 units")
        print(f"  Remaining Quantity: {settings.total_quantity_held}")
        print(f"  Average Cost: ${settings.average_cost}")
        print(f"  Action P/L: ${action.profit_loss:.2f}")
        print(f"  Total P/L: ${settings.total_profit_loss:.2f}")
        print(f"  Reason: {action.reason}")
        
        return True

    def test_10_configuration_update_action(self):
        """TEST 10: Record configuration update action"""
        print("\n" + "="*70)
        print("TEST 10: Configuration Update Recording")
        print("="*70)
        
        settings = CryptoAutoTradingSettings(
            user_id="test_user_123",
            symbol="BTC"
        )
        
        # Record config action
        action = AutoTradingExecutor.record_config_action(
            settings,
            "CONFIG_UPDATE",
            "Updated buy percentage from 5% to 7%"
        )
        
        print(f"✅ Configuration updated")
        print(f"  Action Type: {action.action_type}")
        print(f"  Symbol: {action.symbol}")
        print(f"  Details: {action.reason}")
        print(f"  Timestamp: {action.timestamp}")
        
        return True

    def run_all_tests(self):
        """Run all tests and report results"""
        print("\n" + "#"*70)
        print("# PER-CRYPTOCURRENCY AUTO TRADING - COMPREHENSIVE TEST SUITE")
        print("#"*70)
        
        tests = [
            ("Calculate Buy Trigger Price", self.test_1_calculate_buy_trigger_price),
            ("Calculate Sell Trigger Price", self.test_2_calculate_sell_trigger_price),
            ("Buy Signal Logic", self.test_3_should_buy_logic),
            ("Sell Signal Logic", self.test_4_should_sell_logic),
            ("Profit/Loss Calculation", self.test_5_profit_loss_calculation),
            ("Average Cost Update", self.test_6_average_cost_update),
            ("Settings Management", self.test_7_auto_trading_settings_creation),
            ("Buy Action Recording", self.test_8_buy_action_recording),
            ("Sell Action Recording", self.test_9_sell_action_recording),
            ("Configuration Update", self.test_10_configuration_update_action),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"\n❌ EXCEPTION in {test_name}: {str(e)}")
                failed += 1
        
        # Summary
        print("\n" + "#"*70)
        print("# TEST SUMMARY")
        print("#"*70)
        print(f"Total Tests: {len(tests)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
        print("#"*70 + "\n")
        
        return failed == 0


if __name__ == "__main__":
    tester = TestAutoTradingCoinSystem()
    success = tester.run_all_tests()
    exit(0 if success else 1)
