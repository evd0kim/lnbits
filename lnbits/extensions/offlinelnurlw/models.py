from quart import url_for
from lnurl import Lnurl, LnurlWithdrawResponse, encode as lnurl_encode
from sqlite3 import Row
from typing import NamedTuple
import shortuuid  # type: ignore


class offlinelnurlwLink(NamedTuple):
    id: str
    wallet: str
    title: str
    private_key: str
    amount: int
    used: int
    time: int

    @classmethod
    def from_row(cls, row: Row) -> "offlinelnurlwLink":
        data = dict(row)
        return cls(**data)