import enum
import itertools
import json
import typing
from os.path import dirname, join

GLOBAL_DEFAULTS = json.load(open(join(dirname(__file__), "defaults.json"), "r"))["bookmaker"]


class CommissionType(enum.Enum):
    """How a bookmaker's commission is applied.

    WINNINGS: Commission is taken as a fraction of net winnings (traditional exchanges).
    KALSHI: Prediction-market style fee charged as an entry cost per contract.
    """
    WINNINGS = "winnings"
    KALSHI = "kalshi"


class OddsFormat(enum.Enum):
    """The native format a bookmaker's odds are expressed in."""
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"
    AMERICAN = "american"
    PROBABILITY = "probability"


def _coerce_enum(enum_cls: typing.Type[enum.Enum], value: typing.Any, default: typing.Any) -> enum.Enum:
    """Coerces an enum member / string value / string name / None into an enum member.

    Args:
        enum_cls: The enum class to coerce into.
        value: An enum member, its ``.value``, its name, or None.
        default: The value to use when ``value`` is None (typically the string from DEFAULTS).

    Returns:
        The corresponding enum member.
    """
    if value is None:
        value = default
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)          # match by value, e.g. "winnings"
    except ValueError:
        pass
    try:
        return enum_cls[value]          # match by name, e.g. "WINNINGS"
    except (KeyError, TypeError):
        raise ValueError(
            f"'{value}' is not a valid {enum_cls.__name__}. "
            f"Valid options: {[member.value for member in enum_cls]}")


class Bookmaker:
    DEFAULTS = GLOBAL_DEFAULTS
    __ID_COUNTER = itertools.count()

    def __init__(self,
                 id: typing.Optional[typing.Hashable] = None,
                 commission: typing.Optional[float] = None,
                 wager_limit: typing.Optional[float] = None,
                 ignore_wager_precision: typing.Optional[bool] = None,
                 max_wager_count: typing.Optional[int] = None,
                 lowest_valid_wager: typing.Optional[float] = None,
                 commission_type: typing.Optional[typing.Union[CommissionType, str]] = None,
                 odds_format: typing.Optional[typing.Union[OddsFormat, str]] = None,
                 **kwargs: typing.Any
                 ) -> None:
        """
        Args:
            commission (float): The commission the bookmaker takes (e.g. 5% = 0.05). Defaults to 0.0.
            wager_limit (float): The maximum sum of all wagers with this bookmaker, usually set to balance at bookmaker. Defaults to -1.0 (no limit).
            ignore_wager_precision (bool): If True, Event.wager_precision will be ignored for wagers with this bookmaker. Defaults to False.
            max_wager_count (int): The maximum number of wagers with this bookmaker. Defaults to -1 (no limit).
            lowest_valid_wager (float): The minimum wager size accepted by this bookmaker. Defaults to 0.01.
            commission_type (CommissionType | str): How the commission is applied. Defaults to CommissionType.WINNINGS.
            odds_format (OddsFormat | str): The native format the bookmaker's odds are expressed in. Defaults to OddsFormat.DECIMAL.
        """
        self.id = id if id is not None else next(self.__ID_COUNTER)
        self.commission = self.DEFAULTS["commission"] if commission is None else float(commission)
        self.wager_limit = self.DEFAULTS["wager_limit"] if wager_limit is None else float(wager_limit)
        self.ignore_wager_precision = self.DEFAULTS["ignore_wager_precision"] if ignore_wager_precision is None else ignore_wager_precision
        self.max_wager_count = self.DEFAULTS["max_wager_count"] if max_wager_count is None else max_wager_count
        self.lowest_valid_wager = self.DEFAULTS["lowest_valid_wager"] if lowest_valid_wager is None else float(lowest_valid_wager)
        self.commission_type = _coerce_enum(CommissionType, commission_type, self.DEFAULTS["commission_type"])
        self.odds_format = _coerce_enum(OddsFormat, odds_format, self.DEFAULTS["odds_format"])

        self.__kwargs: typing.Dict[str, typing.Any] = kwargs

        # self._id = next(self.__ID_COUNTER)

    def as_dict(self, verbose: bool = False, necessary_keys_only: bool = True) -> typing.Dict[str, typing.Any]:
        """Returns the bookmaker as a dictionary.

        Args:
            verbose (bool): If True, all attributes will be returned, even if they match their default value.
            necessary_keys_only (bool): If True, only the keys that are necessary to process the event will be returned.

        Returns:
            dict: The bookmaker as a dictionary.
        """
        necessary_keys = ["id"] + list(GLOBAL_DEFAULTS.keys())
        basic_result = {}
        for key, value in self.__dict__.copy().items():
            if isinstance(value, enum.Enum):            # serialize enums by their string value
                value = value.value
            if not verbose and value == self.DEFAULTS.get(key, None):
                continue
            if necessary_keys_only and key not in necessary_keys:
                continue
            basic_result[key] = value
        # basic_result.pop("_id", None)
        basic_result.pop("_Bookmaker__kwargs", None)
        return {**basic_result, **self.__kwargs}

    @classmethod
    def from_dict(cls: typing.Type['BOOKMAKER_T'], _bookmaker_dict: dict) -> 'BOOKMAKER_T':
        """Creates a bookmaker from a dictionary.

            Args:
                __bookmaker_dict (dict): The dictionary to create the bookmaker from.

            Returns:
                Bookmaker: The bookmaker created from the dictionary.
        """
        id_key = "id"
        if "_id" in _bookmaker_dict:
            id_key = "_id"

        _bookmaker_dict = {**GLOBAL_DEFAULTS, **_bookmaker_dict} # Ensure default keys are present
        bookmaker = cls(**_bookmaker_dict)
        # bookmaker._id = _bookmaker_dict.get(id_key, bookmaker._id)  # override the generated id
        return bookmaker

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Bookmaker):
            raise NotImplementedError
        return self.id == __value.id

BOOKMAKER_T = typing.Union[typing.TypeVar('BOOKMAKER_T', bound='Bookmaker'), Bookmaker]
