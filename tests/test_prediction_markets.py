import unittest

import betting_event as b_event
from betting_event.bet import Bet, BetType
from betting_event.bookmaker import Bookmaker, CommissionType, OddsFormat
from betting_event.utils import (american_to_decimal, decimal_to_american,
                                 decimal_to_fractional,
                                 decimal_to_probability, fractional_to_decimal,
                                 from_decimal, kalshi_fee,
                                 probability_to_decimal, to_decimal)


class TestKalshiFee(unittest.TestCase):
    def test_fee_table(self):
        self.assertEqual(kalshi_fee(100, 0.5), 1.75)
        self.assertEqual(kalshi_fee(1, 0.5), 0.02)
        self.assertEqual(kalshi_fee(100, 0.5, 0.0175), 0.44)

    def test_exact_whole_cent_not_rounded_up(self):
        # 0.07 * 100 * 0.25 * 100 = 175 cents exactly -> 1.75, not 1.76
        self.assertEqual(kalshi_fee(100, 0.5), 1.75)

    def test_symmetry(self):
        for price in (0.1, 0.25, 0.4, 0.42, 0.75):
            self.assertEqual(kalshi_fee(100, price), kalshi_fee(100, 1 - price))

    def test_aggregate_round_up(self):
        # A single contract's raw fee is tiny but rounds up to a whole cent.
        self.assertEqual(kalshi_fee(1, 0.5), 0.02)


class TestOddsConversions(unittest.TestCase):
    def test_probability_round_trip(self):
        self.assertEqual(probability_to_decimal(0.4), 2.5)
        self.assertEqual(decimal_to_probability(2.5), 0.4)
        self.assertEqual(decimal_to_probability(probability_to_decimal(0.25)), 0.25)

    def test_probability_bounds(self):
        self.assertRaises(ValueError, probability_to_decimal, 0.0)
        self.assertRaises(ValueError, probability_to_decimal, 1.0)
        self.assertRaises(ValueError, probability_to_decimal, 1.5)

    def test_dispatch_to_decimal(self):
        self.assertEqual(to_decimal(2.5, OddsFormat.DECIMAL), 2.5)
        self.assertEqual(to_decimal("3/2", OddsFormat.FRACTIONAL), fractional_to_decimal("3/2"))
        self.assertEqual(to_decimal(150, OddsFormat.AMERICAN), american_to_decimal(150))
        self.assertEqual(to_decimal(0.4, OddsFormat.PROBABILITY), 2.5)

    def test_dispatch_accepts_strings(self):
        self.assertEqual(to_decimal(0.4, "probability"), 2.5)
        self.assertEqual(to_decimal(0.4, "PROBABILITY"), 2.5)
        self.assertEqual(from_decimal(2.5, "probability"), 0.4)

    def test_dispatch_from_decimal(self):
        self.assertEqual(from_decimal(2.5, OddsFormat.DECIMAL), 2.5)
        self.assertEqual(from_decimal(2.5, OddsFormat.PROBABILITY), 0.4)
        self.assertEqual(from_decimal(2.5, OddsFormat.AMERICAN), decimal_to_american(2.5))
        self.assertEqual(from_decimal(2.5, OddsFormat.FRACTIONAL), decimal_to_fractional(2.5))


class TestBookmakerEnums(unittest.TestCase):
    def test_defaults(self):
        # Explicit ids throughout so the shared auto-id counter is left untouched
        # (other test modules assert on specific auto-assigned ids).
        bookmaker = Bookmaker(id=100)
        self.assertEqual(bookmaker.commission_type, CommissionType.WINNINGS)
        self.assertEqual(bookmaker.odds_format, OddsFormat.DECIMAL)

    def test_coercion(self):
        self.assertEqual(Bookmaker(commission_type="kalshi", id=101).commission_type, CommissionType.KALSHI)
        self.assertEqual(Bookmaker(commission_type="KALSHI", id=102).commission_type, CommissionType.KALSHI)
        self.assertEqual(Bookmaker(commission_type=CommissionType.KALSHI, id=103).commission_type, CommissionType.KALSHI)
        self.assertEqual(Bookmaker(odds_format="probability", id=104).odds_format, OddsFormat.PROBABILITY)

    def test_invalid_enum(self):
        self.assertRaises(ValueError, Bookmaker, commission_type="nonsense", id=105)

    def test_as_dict_round_trip(self):
        bookmaker = Bookmaker(commission=0.07, commission_type="kalshi", odds_format="probability", id=7)
        as_dict = bookmaker.as_dict()
        self.assertEqual(as_dict["commission_type"], "kalshi")
        self.assertEqual(as_dict["odds_format"], "probability")
        rebuilt = Bookmaker.from_dict(as_dict)
        self.assertEqual(rebuilt.commission_type, CommissionType.KALSHI)
        self.assertEqual(rebuilt.odds_format, OddsFormat.PROBABILITY)

    def test_default_as_dict_omits_new_keys(self):
        # Backward compatibility: a default bookmaker must not emit the new keys.
        as_dict = Bookmaker(id=3).as_dict(necessary_keys_only=False)
        self.assertNotIn("commission_type", as_dict)
        self.assertNotIn("odds_format", as_dict)


class TestBetProbabilityOdds(unittest.TestCase):
    def test_probability_bet_stores_decimal_emits_probability(self):
        kalshi = Bookmaker(commission=0.07, commission_type="kalshi", odds_format="probability", id=11)
        bet = Bet(BetType.MatchWinner, "home", 0.4, bookmaker=kalshi)
        # stored canonically as decimal
        self.assertEqual(bet.odds, 2.5)
        # emitted back in native (probability) format
        self.assertEqual(bet.as_dict()["odds"], 0.4)

    def test_decimal_bet_unchanged(self):
        bet = Bet(BetType.MatchWinner, "home", 2.5)
        self.assertEqual(bet.odds, 2.5)
        self.assertEqual(bet.as_dict()["odds"], 2.5)


if __name__ == "__main__":
    unittest.main()
