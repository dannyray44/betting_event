import math

def american_to_decimal(american_odds: int) -> float:
    """Converts American odds to decimal odds."""
    if american_odds >= 100:
        decimal_odds = 1 + (american_odds / 100)
    else:
        decimal_odds = (100 / abs(american_odds)) + 1
    return round(decimal_odds, 2)

def decimal_to_american(decimal_odds: float) -> int:
    """Converts decimal odds to American odds."""
    if decimal_odds >= 2:
        american_odds = (decimal_odds - 1) * 100
    else:
        american_odds = -100 / (decimal_odds - 1)
    return int(american_odds)

def fractional_to_decimal(fractional_odds: str) -> float:
    """Converts fractional odds to decimal odds."""
    numerator, denominator = map(int, fractional_odds.split('/'))
    decimal_odds = 1 + (numerator / denominator)
    return round(decimal_odds, 2)

def decimal_to_fractional(decimal_odds: float) -> str:
    """Converts decimal odds to fractional odds. Ensuring the fraction is in its simplest form."""
    numerator = decimal_odds - 1
    denominator = 1
    while not numerator.is_integer():
        numerator *= 10
        denominator *= 10
    numerator = int(numerator)
    denominator = int(denominator)
    gcd = math.gcd(numerator, denominator)
    numerator /= gcd
    denominator /= gcd
    return f'{int(numerator)}/{int(denominator)}'

def probability_to_decimal(probability: float) -> float:
    """Converts an implied probability (0 < p < 1) to decimal odds."""
    if not 0.0 < probability < 1.0:
        raise ValueError(f"Probability '{probability}' is not valid. Must be a float strictly between 0 and 1.")
    return round(1 / probability, 4)

def decimal_to_probability(decimal_odds: float) -> float:
    """Converts decimal odds to an implied probability."""
    return round(1 / decimal_odds, 4)

# Odds format string values. Kept as plain strings (not enum imports) so that
# utils.py has no dependency on bookmaker.py, avoiding a circular import.
_DECIMAL = "decimal"
_FRACTIONAL = "fractional"
_AMERICAN = "american"
_PROBABILITY = "probability"

def _normalise_odds_format(odds_format) -> str:
    """Coerces an OddsFormat enum member, its value or its name into a lowercase string value."""
    fmt = getattr(odds_format, "value", odds_format)
    if isinstance(fmt, str):
        fmt = fmt.lower()
    return fmt

def to_decimal(value, odds_format) -> float:
    """Converts odds in the given format into canonical decimal odds.

    Args:
        value: The odds in the native format (float, int or str depending on format).
        odds_format: An OddsFormat enum member or its string value/name.

    Returns:
        float: The odds expressed as decimal odds.
    """
    fmt = _normalise_odds_format(odds_format)
    if fmt == _DECIMAL:
        return float(value)
    if fmt == _FRACTIONAL:
        return fractional_to_decimal(value)
    if fmt == _AMERICAN:
        return american_to_decimal(int(value))
    if fmt == _PROBABILITY:
        return probability_to_decimal(float(value))
    raise ValueError(f"Unknown odds format: {odds_format!r}")

def from_decimal(decimal_odds: float, odds_format):
    """Converts canonical decimal odds back into the given native format.

    Args:
        decimal_odds (float): The decimal odds.
        odds_format: An OddsFormat enum member or its string value/name.

    Returns:
        The odds expressed in the requested native format.
    """
    fmt = _normalise_odds_format(odds_format)
    if fmt == _DECIMAL:
        return float(decimal_odds)
    if fmt == _FRACTIONAL:
        return decimal_to_fractional(decimal_odds)
    if fmt == _AMERICAN:
        return decimal_to_american(decimal_odds)
    if fmt == _PROBABILITY:
        return decimal_to_probability(decimal_odds)
    raise ValueError(f"Unknown odds format: {odds_format!r}")

def kalshi_fee(contracts: float, price: float, multiplier: float = 0.07) -> float:
    """Returns the Kalshi trading fee for an aggregate order.

    Kalshi charges ``ceil(multiplier * contracts * price * (1 - price)))`` in cents,
    rounded up to the next whole cent on the AGGREGATE order (not per contract).

    Args:
        contracts (float): The number of contracts in the order.
        price (float): The per-contract price (implied probability, 0 < price < 1).
        multiplier (float): The fee multiplier. Defaults to 0.07.

    Returns:
        float: The fee in currency units (e.g. dollars).
    """
    raw_cents = multiplier * contracts * price * (1 - price) * 100
    # round(..., 9) strips floating point noise so an exact whole-cent fee is not
    # nudged up to the next cent (e.g. kalshi_fee(100, 0.5) == 1.75, not 1.76).
    return math.ceil(round(raw_cents, 9)) / 100
