import enum
import json
import re
import typing
from os.path import dirname, join

from .bookmaker import BOOKMAKER_T, Bookmaker
from .utils import from_decimal, to_decimal


class BetType(enum.Enum):
    """Enum of currently accepted bet types"""
    MatchWinner = 1
    AsianHandicap = 2
    Goals_OverUnder = 3  
    BothTeamsToScore = 4
    ExactScore = 5
    DoubleChance = 6
    Team_OverUnder = 7
    OddEven = 8
    Team_OddEven = 9
    Result_BothTeamsScore = 10
    Result_OverUnder = 11
    TeamCleanSheet = 12
    Team_WinToNil = 13
    TotalGoals = 14
    Team_ExactGoals = 15
    Team_ScoreAGoal = 16
    DrawNoBet = 17

    Team_GoalsRange = 18
    BothTeamsToScore_OverUnder = 19
    TotalGoalsRange = 20

ValueCheck: typing.Dict[BetType, typing.Tuple[typing.Pattern, str, typing.List[str]]] = {
    BetType.MatchWinner:            (re.compile(r"^(home|draw|away)$", re.IGNORECASE), 
        "Value string must be `home` `draw` or `away`.",
        ['home', 'draw', 'away']),

    BetType.AsianHandicap:          (re.compile(r"^(home|away) ([+-]?\d+(?:\.(?:0|25|5|75))?)$", re.IGNORECASE),
        """Value string must be formatted as `TEAM NUMBER`:
            TEAM: Must be `home` or `away`.
            NUMBER: Must be a float divisible by 0.25 (Or 0.0). Negative and positive values are valid.""",
        ['home -0.75', 'away -3.0', 'home 4.25', 'away 1.75']),

    BetType.Goals_OverUnder:        (re.compile(r"^(over|under) ([+-]?\d+(?:\.(?:0|25|5|75))?)$", re.IGNORECASE),
        """Value string must be formatted as `POSITION NUMBER`:
            POSITION: Must be `over` or `under`.
            NUMBER: Must be a float divisible by 0.25.""",
        ['over 0.75', 'under 3.0', 'over 4.25', 'under 1.75']),

    BetType.BothTeamsToScore:       (re.compile(r"^(yes|no)$", re.IGNORECASE),
        "Value string must be either `yes` or `no`",
        ['yes', 'no']),

    BetType.ExactScore:             (re.compile(r"([0-9]{1,4}):([0-9]{1,4})"),
        """Value string must contain at least one `HOME_SCORE:AWAY_SCORE`:
            HOME_SCORE and AWAY_SCORE: Must be an integer number between 0 and 9999.
            Multiple scores can be separated by a space (or comma). E.g. `2:1 0:0 0:1 1:1""",
        ['2:1', '0:0 0:1 1:1']),

    BetType.DoubleChance:           (re.compile(r"^(home|draw|away)\/(home|draw|away)$", re.IGNORECASE),
        """Value string must be formatted as `RESULT_A/RESULT_B`
            RESULT_A and RESULT_B: Must be `home`, `draw` or `away`. And RESULT_A != RESULT_B""",
        ['home/draw', 'home/away', 'draw/home', 'draw/away', 'away/home', 'away/draw']),

    BetType.Team_OverUnder:         (re.compile(r"^(home|away) (over|under) ([0-9]{1,4}).5$", re.IGNORECASE),
        """Value string must be formatted as `TEAM POSITION NUMBER`:
            TEAM: Must be `home` or `away`.
            POSITION: Must be `over` or `under`.
            NUMBER: Must a float divisible by 0.5 between 0.5 and 9999.5.""",
        ['home over 2.5', 'away under 0.5']),

    BetType.OddEven:                (re.compile(r"^(odd|even)$", re.IGNORECASE),
        """Value string must be either `odd` or `even`""",
        ['odd', 'even']),

    BetType.Team_OddEven:           (re.compile(r"^(home|away) (odd|even)$", re.IGNORECASE),
        """Value string must be formatted as `TEAM EVENNESS`:
            TEAM: Must be `home` or `away`.
            EVENNESS: Must be `odd` or `even`""",
        ['home odd', 'away even', 'home even', 'away odd']), 

    BetType.Result_BothTeamsScore:  (re.compile(r"^(home|draw|away)\/(yes|no)$", re.IGNORECASE),
        """Value string must be formatted as `RESULT/SWITCH`:
            RESULT: Must be `home`, `draw` or `away`.
            SWITCH: Must be `yes` or `no`""",
        ['home/yes', 'draw/no', 'away/yes','home/no', 'draw/yes', 'away/no']),

    BetType.Result_OverUnder:       (re.compile(r"^(home|draw|away)\/(over|under) ([0-9]{1,4}).5$", re.IGNORECASE),
        """Value string must be formatted as `RESULT/POSITION NUMBER`:
            RESULT: Must be `home`, `draw` or `away`.
            POSITION: Must be `over` or `under`.
            NUMBER: Must be a float divisible by 0.5. Only positive values are valid.""",
        ['home/over 2.5', 'draw/under 3.5', 'away/over 4.5', 'draw/under 0.5']),

    BetType.TeamCleanSheet:         (re.compile(r"^(home|away) (yes|no)$", re.IGNORECASE),
        """Value string must be formatted as `TEAM CLEAN_SHEET`:
            TEAM: Must be `home` or `away`.
            CLEAN_SHEET: Must be `yes` or `no`""",
        ['home yes', 'away no']),

    BetType.Team_WinToNil:          (re.compile(r"^(home|away) (yes|no)$", re.IGNORECASE),
        """Value string must be formatted as `TEAM WIN_TO_NIL`:
            TEAM: Must be `home` or `away`.
            WIN_TO_NIL: Must be `yes` or `no`""",
        ['home no', 'away yes', 'home yes', 'away no']),

    BetType.TotalGoals:             (re.compile(r"^([0-9]{1,4})$"),
        """Value string must be formatted as an integer.""",
        ['2', '3', '4']),

    BetType.Team_ExactGoals:        (re.compile(r"^(home|away) ([0-9]{1,4})$", re.IGNORECASE),
        """Value string must be formatted as `TEAM NUMBER`:
            TEAM: Must be `home` or `away`.
            NUMBER: Must be a positive integer.""",
            ['home 2', 'away 3']),

    BetType.Team_ScoreAGoal:        (re.compile(r"^(home|away) (yes|no)$", re.IGNORECASE),
        """Value string must be formatted as `TEAM SWITCH`:
            TEAM: Must be `home` or `away`.
            SWITCH: Must be `yes` or `no`""",
        ['home yes', 'away no', 'home no', 'away yes']),

    BetType.DrawNoBet:              (re.compile(r"^(home|away)$", re.IGNORECASE),
        """Value string must be formatted as `TEAM`:
            TEAM: Must be `home` or `away`""",
        ['home', 'away']),

    BetType.Team_GoalsRange:        (re.compile(r"^(home|away) ([0-9]{1,4})-([0-9]{1,4})$", re.IGNORECASE),
        """Value string must be formatted as `TEAM MIN-MAX`:
            TEAM: Must be `home` or `away`.
            MIN: Must be a positive integer.
            MAX: Must be a positive integer greater than MIN.""",
        ['home 2-3', 'away 4-5']),

    BetType.BothTeamsToScore_OverUnder: (re.compile(r"^(yes|no) (over|under) ([0-9]{1,4}).5$", re.IGNORECASE),
        """Value string must be formatted as `SWITCH POSITION NUMBER`:
            SWITCH: Must be `yes` or `no`.
            POSITION: Must be `over` or `under`.
            NUMBER: Must be a float divisible by 0.5.""",
        ['yes over 2.5', 'no under 3.5']),

    BetType.TotalGoalsRange:        (re.compile(r"^([0-9]{1,4})-([0-9]{1,4})$"),
        """Value string must be formatted as `MIN-MAX`:
            MIN: Must be a positive integer.
            MAX: Must be a positive integer greater than MIN.""",
        ['2-3', '4-6']),
}

DefaultsType = typing.TypedDict("DefaultsType", {
    "bookmaker": BOOKMAKER_T,
    "lay": bool,
    "volume": float,
    "previous_wager": float,
    "wager": float
})

GLOBAL_DEFAULTS: DefaultsType = json.load(open(join(dirname(__file__), "defaults.json"), "r"))["bet"]
GLOBAL_DEFAULTS["bookmaker"] = Bookmaker()

class Bet:
    DEFAULTS: DefaultsType = GLOBAL_DEFAULTS

    def __init__(self,
                 bet_type: typing.Union[BetType, int, str],
                 value: str,
                 odds: float,
                #  *args,
                 bookmaker: typing.Optional[Bookmaker] = None,
                 lay: typing.Optional[bool] = None,
                 volume: typing.Optional[float] = None,
                 previous_wager: typing.Optional[float] = None, 
                 wager: typing.Optional[float] = None,
                 **kwargs: typing.Any
                 ) -> None:
        """Bet class constructor

        Args:
            bet_type (BetType | int): Bet type or bet type int as defined in bet.BetType.
            value (str): Bet value. The accepted inputs of this is dependent on the bet_type.
            odds (float): The odds for the bet.
            bookmaker (Bookmaker | None): The bookmaker for the bet. If
            not provided, the default bookmaker with no limits will be used.
            volume (float): The volume for the bet (only applies to exchanges). DEFAULTS
            to -1.0, meaning no volume specified.
            lay (bool): True if the bet is a lay bet, False if it is a back bet.
            previous_wager (float): The sum of any previous wagers placed on this bet.
            DEFAULTS to 0.0. Useful for when a bet has been partially matched and you want to
            recalculate.
        """

        # bookmaker = self.DEFAULTS["bookmaker"] if bookmaker is None else bookmaker
        # if not issubclass(type(bookmaker), Bookmaker):
            # _temp_bookmaker = Bookmaker()
            # _temp_bookmaker._id = bookmaker
            # bookmaker = _temp_bookmaker

        if bookmaker is None:
            bookmaker = self.DEFAULTS["bookmaker"]
        self.bookmaker: Bookmaker = bookmaker if issubclass(type(bookmaker), Bookmaker) else Bookmaker(id= bookmaker)

        self.bet_type: BetType = BetType(bet_type) if not isinstance(bet_type, str) else BetType[bet_type]

        self.value: str = value
        # Store odds canonically as decimal, converting from the bookmaker's native
        # odds format. Must run before any odds > 1.0 validation (in from_dict).
        self.odds: float = to_decimal(odds, self.bookmaker.odds_format)
        if lay is None:
            lay = self.DEFAULTS["lay"]
        self.lay: bool = lay if not isinstance(lay, str) else (lay.lower() != "false")
        self.volume: float = self.DEFAULTS['volume'] if volume is None else float(volume) 
        self.previous_wager: float = self.DEFAULTS['previous_wager'] if previous_wager is None else float(previous_wager)
        self.wager: float = self.DEFAULTS['wager'] if wager is None else float(wager)
        self.__kwargs: typing.Dict[str, typing.Any] = kwargs

        _matches = ValueCheck[self.bet_type][0].findall(self.value)

        if not _matches or not _matches[0]:
            raise ValueError( f"Bet value '{self.value}' is not valid for bet type " +
                f"{self.bet_type.name} ({self.bet_type.value}).\nExpected regex format: " +
                f"'{ValueCheck[self.bet_type][0].pattern}'\n{ValueCheck[self.bet_type][1]}")

    def __eq__(self, __new_bet: object) -> bool:
        if not isinstance(__new_bet, Bet):
            raise NotImplementedError
        return self.bet_type == __new_bet.bet_type and self.bookmaker == __new_bet.bookmaker and \
            self.value == __new_bet.value and self.odds == __new_bet.odds and self.lay == __new_bet.lay

    def __hash__(self) -> int:
        return hash((self.bet_type, self.bookmaker.id, self.value, self.odds, self.lay))

    def update_from_bet(self, __new_bet: 'Bet') -> None:
        """Updates this bet from another bet.

        Args:
            __new_bet (Bet): The bet to update from.
        """
        for key in self.DEFAULTS.keys():
            if key in ["bookmaker", "bet_type", "value", "odds", "lay"]:
                continue
            setattr(self, key, getattr(__new_bet, key))

    def as_dict(self, verbose: bool = False, necessary_keys_only: bool = True) -> dict:
        """Returns the bet as a dictionary.

        Args:
            verbose (bool): If True, default values will be included in the dictionary. Defaults to False.
            necessary_keys_only (bool): If True, only the keys necessary for wager calculation are included. Defaults to True.

        Returns:
            dict: This bet represented as a dictionary.
        """

        result: dict = self.__dict__.copy()
        necessary_keys = ["bet_type", "value", "odds"] + list(GLOBAL_DEFAULTS.keys())

        if not verbose or necessary_keys_only:
            for key in list(result.keys()):
                if (not verbose and result[key] == self.DEFAULTS.get(key, None)) or (necessary_keys_only and key not in necessary_keys):
                    del result[key]

        result["bet_type"] = self.bet_type.name
        if "odds" in result:
            # Emit odds back in the bookmaker's native format so (odds_format, odds) round-trips.
            result["odds"] = from_decimal(self.odds, self.bookmaker.odds_format)
        if "bookmaker" in result:
            result["bookmaker"] = self.bookmaker.id

        return result

    @classmethod
    def from_dict(cls, bet_dict: dict) -> 'Bet':
        """Creates a bet from a dictionary. Slower that using the constructor but with added error checking.

        Args:
            bet_dict (dict): The dictionary to create the bet from.

        Returns:
            str: The error message if the bet could not be created.
        """
        printable_dict = bet_dict.copy()
        if "bookmaker" in bet_dict and hasattr(bet_dict["bookmaker"], "id"):
            printable_dict["bookmaker"] = bet_dict["bookmaker"].id

        for required_key in ["bet_type", "value", "odds"]:
            if required_key not in bet_dict:
                raise KeyError(f"Missing required key '{required_key}' in bet_dict: {printable_dict}")

        try:
            new_bet = cls(**bet_dict)
        except TypeError as e:
            raise TypeError(f"A value in bet is of the wrong type (e.g a list instead of a float): {printable_dict}")
        except KeyError as e:
            raise KeyError(f"KeyError, likely due to invalid bet_type: {printable_dict}")

        if new_bet.odds <= 1.0:
            raise ValueError(f"Bet odds '{new_bet.odds}' is not valid. Must be a positive float greater than 1.0. AKA decimal odds format.")
        if new_bet.volume < 0.0 and new_bet.volume != -1.0:
            raise ValueError(f"Bet volume '{new_bet.volume}' is not valid. Must be a positive float or -1.0.")
        if new_bet.previous_wager < 0.0:
            raise ValueError(f"Bet previous_wager '{new_bet.previous_wager}' is not valid. Must be a non negative float.")

        return new_bet

    def wager_placed(self, wager_size: typing.Optional[float] = None) -> float:
        "Sets the wager placed to the previous wager + the current wager. Also resets the current wager."
        if wager_size is None:
            self.previous_wager += self.wager
        else:
            self.previous_wager += wager_size
        # self.wager = 0.0
        return self.previous_wager

    def exposure(self, wager: typing.Optional[float] = None) -> float:
        """Returns the exposure (amount that could be lost) of the bet given a wager. If no wager is provided, self.previous_wager will be used.

        Args:
            wager (float): The wager to calculate the exposure for. If not provided, self.previous_wager will be used.

        Returns:
            float: The exposure for this bet.
        """
        if wager is None:
            wager = self.previous_wager

        if self.lay:
            return wager * (self.odds - 1.0)
        return wager

BET_T = typing.Union[typing.TypeVar('BET_T', bound='Bet'), Bet]
