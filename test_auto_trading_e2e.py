#!/usr/bin/env python3
"""
CryptoAI Auto Trading End-to-End Test Suite

Tests the complete auto trading flow:
1. Authentication
2. Binance connection
3. Trade preview calculation
4. Trade execution
5. MongoDB persistence
6. Active trades retrieval
"""

import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Configuration
load_dotenv()
API_BASE = "http://localhost:8002"
TEST_USER = "testuser_autotrading"
TEST_PASSWORD = "TestPassword123!"
TRADE_SYMBOL = "BTCUSDT"
TRADE_QUANTITY = 0.001
STOP_LOSS = 59000
TAKE_PROFIT = 65000

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def print_test(text, passed):
    if passed:
        print_success(text)
    else:
        print_error(text)
    return passed

class AutoTradingTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }

    def add_result(self, name, passed, message=""):
        status = "PASS" if passed else "FAIL"
        self.results["tests"].append({
            "name": name,
            "status": status,
            "message": message
        })
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1

    def test_health_check(self):
        """Test 1: Backend health check"""
        print_header("Test 1: Backend Health Check")
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            if response.status_code == 200:
                print_success(f"Backend health: {response.json()}")
                self.add_result("Health Check", True)
                return True
            else:
                print_error(f"Backend returned {response.status_code}")
                self.add_result("Health Check", False)
                return False
        except Exception as e:
            print_error(f"Backend unreachable: {e}")
            self.add_result("Health Check", False)
            return False

    def test_login(self):
        """Test 2: User authentication"""
        print_header("Test 2: User Authentication")
        try:
            payload = {
                "username": TEST_USER,
                "password": TEST_PASSWORD
            }
            response = requests.post(
                f"{API_BASE}/api/auth/login",
                json=payload,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                if self.token:
                    print_success(f"Login successful")
                    print_info(f"User: {data.get('username')}")
                    print_info(f"Tier: {data.get('tier')}")
                    self.add_result("Login", True)
                    return True
            print_error(f"Login failed: {response.status_code} - {response.text}")
            self.add_result("Login", False)
            return False
        except Exception as e:
            print_error(f"Login request failed: {e}")
            self.add_result("Login", False)
            return False

    def test_subscription_status(self):
        """Test 3: Check subscription tier"""
        print_header("Test 3: Subscription Status")
        if not self.token:
            print_error("Not authenticated - skipping test")
            self.add_result("Subscription Status", False)
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{API_BASE}/api/subscription/status",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                tier = data.get("tier")
                if tier == "premium":
                    print_success(f"User has {tier.upper()} tier (auto trading enabled)")
                    self.add_result("Subscription Status", True)
                    return True
                else:
                    print_error(f"User tier is '{tier}' - needs 'premium' for auto trading")
                    self.add_result("Subscription Status", False)
                    return False
            print_error(f"Status check failed: {response.status_code}")
            self.add_result("Subscription Status", False)
            return False
        except Exception as e:
            print_error(f"Subscription request failed: {e}")
            self.add_result("Subscription Status", False)
            return False

    def test_binance_status(self):
        """Test 4: Binance connection"""
        print_header("Test 4: Binance Connection")
        if not self.token:
            print_error("Not authenticated - skipping test")
            self.add_result("Binance Status", False)
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{API_BASE}/api/binance/status",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("connected"):
                    print_success(f"Connected to Binance {'TESTNET' if data.get('testnet') else 'MAINNET'}")
                    print_info(f"Account balance: {data.get('account_balance')} USDT")
                    self.add_result("Binance Status", True)
                    return True
                else:
                    print_error("Binance not connected")
                    self.add_result("Binance Status", False)
                    return False
            print_error(f"Binance status check failed: {response.status_code}")
            self.add_result("Binance Status", False)
            return False
        except Exception as e:
            print_error(f"Binance status request failed: {e}")
            self.add_result("Binance Status", False)
            return False

    def test_trade_preview(self):
        """Test 5: Trade preview calculation"""
        print_header("Test 5: Trade Preview Calculation")
        if not self.token:
            print_error("Not authenticated - skipping test")
            self.add_result("Trade Preview", False)
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "symbol": TRADE_SYMBOL,
                "action": "BUY",
                "quantity": TRADE_QUANTITY,
                "stop_loss": STOP_LOSS,
                "take_profit": TAKE_PROFIT,
                "acknowledgement_risks_understood": True,
                "acknowledgement_terms_accepted": True
            }
            response = requests.post(
                f"{API_BASE}/api/auto-trading/preview",
                json=payload,
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print_success("Trade preview calculated")
                print_info(f"  Symbol: {data.get('symbol')}")
                print_info(f"  Action: {data.get('action')}")
                print_info(f"  Quantity: {data.get('quantity')}")
                print_info(f"  Max Loss: ${data.get('max_estimated_loss'):.2f}")
                print_info(f"  Max Gain: ${data.get('max_estimated_gain'):.2f}")
                self.add_result("Trade Preview", True)
                return True
            else:
                print_error(f"Preview failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.add_result("Trade Preview", False)
                return False
        except Exception as e:
            print_error(f"Preview request failed: {e}")
            self.add_result("Trade Preview", False)
            return False

    def test_trade_execution(self):
        """Test 6: Execute actual trade"""
        print_header("Test 6: Trade Execution (OPTIONAL)")
        print_info("This test will execute a REAL trade on Binance")
        if not self.token:
            print_error("Not authenticated - skipping test")
            self.add_result("Trade Execution", False)
            return False
        
        response = input("Continue with real trade execution? (yes/no): ").lower()
        if response != "yes":
            print_info("Trade execution skipped")
            self.add_result("Trade Execution", False, "Skipped by user")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "symbol": TRADE_SYMBOL,
                "action": "BUY",
                "quantity": TRADE_QUANTITY,
                "stop_loss": STOP_LOSS,
                "take_profit": TAKE_PROFIT,
                "acknowledgement_risks_understood": True,
                "acknowledgement_terms_accepted": True
            }
            response = requests.post(
                f"{API_BASE}/api/auto-trading/execute",
                json=payload,
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print_success("Trade executed successfully")
                print_info(f"  Order ID: {data.get('order_id')}")
                print_info(f"  Status: {data.get('status')}")
                self.add_result("Trade Execution", True)
                return True
            else:
                print_error(f"Execution failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.add_result("Trade Execution", False)
                return False
        except Exception as e:
            print_error(f"Execution request failed: {e}")
            self.add_result("Trade Execution", False)
            return False

    def test_active_trades(self):
        """Test 7: Retrieve active trades"""
        print_header("Test 7: Active Trades Retrieval")
        if not self.token:
            print_error("Not authenticated - skipping test")
            self.add_result("Active Trades", False)
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{API_BASE}/api/auto-trading/user/active-trades",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                trades = data.get("active_trades", [])
                print_success(f"Retrieved {len(trades)} active trades")
                for i, trade in enumerate(trades[:3]):  # Show first 3
                    print_info(f"  Trade {i+1}: {trade.get('symbol')} {trade.get('action')} {trade.get('quantity')}")
                self.add_result("Active Trades", True)
                return True
            else:
                print_error(f"Failed to retrieve trades: {response.status_code}")
                self.add_result("Active Trades", False)
                return False
        except Exception as e:
            print_error(f"Active trades request failed: {e}")
            self.add_result("Active Trades", False)
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        print_header("CryptoAI Auto Trading E2E Test Suite")
        print_info(f"API Base: {API_BASE}")
        print_info(f"Test User: {TEST_USER}")
        print_info(f"Test Time: {datetime.now().isoformat()}")
        
        # Run tests in sequence
        self.test_health_check()
        if not self.token:
            self.test_login()
        
        if self.token:
            self.test_subscription_status()
            self.test_binance_status()
            self.test_trade_preview()
            self.test_trade_execution()
            self.test_active_trades()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")
        passed = self.results["passed"]
        failed = self.results["failed"]
        total = passed + failed
        
        print(f"Tests Run: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        if failed > 0:
            print(f"{RED}Failed: {failed}{RESET}")
        
        print("\nDetailed Results:")
        for test in self.results["tests"]:
            status_color = GREEN if test["status"] == "PASS" else RED
            print(f"  {status_color}[{test['status']}]{RESET} {test['name']}")
            if test["message"]:
                print(f"         {test['message']}")
        
        print("\n" + "="*60)
        if failed == 0:
            print_success("All tests passed! Auto trading is ready.")
        else:
            print_error(f"{failed} test(s) failed. Check configuration and try again.")
        print("="*60)

if __name__ == "__main__":
    tester = AutoTradingTester()
    tester.run_all_tests()
