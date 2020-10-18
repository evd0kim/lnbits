from datetime import datetime
from typing import List, Optional, Union
from lnbits.db import open_ext_db
from lnbits.helpers import urlsafe_short_hash

from .models import offlinelnurlwLink
import ecdsa
from hashlib import sha256


def create_offlinelnurlw_link(
    title: str,
    wallet_id: str,
) -> offlinelnurlwLink:
    print("poo")
    with open_ext_db("offlinelnurlw") as db:

        link_id = urlsafe_short_hash()
        private_key = urlsafe_short_hash()
        db.execute(
            """
            INSERT INTO offlinelnurlw_link (
                id,
                title,
                wallet,
                private_key, 
                amount,
                used
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                link_id,
                title,
                wallet_id,
                private_key,
                0,
                0,
            ),
        )
    return get_offlinelnurlw_link(link_id, 0)


def get_offlinelnurlw_link(link_id: str, hash_id=None, num=0) -> Optional[offlinelnurlwLink]:
    with open_ext_db("offlinelnurlw") as db:
        row = db.fetchone("SELECT * FROM offlinelnurlw_link WHERE id = ?", (link_id,))
    if hash_id:
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(link_id), curve=ecdsa.SECP256k1, hashfunc=sha256)
        if not vk.verify(bytes.fromhex(row[3]), hash_id):
            return None

    return offlinelnurlwLink(**row) if row else None


def get_offlinelnurlw_links(wallet_ids: Union[str, List[str]]) -> List[offlinelnurlwLink]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    with open_ext_db("offlinelnurlw") as db:
        q = ",".join(["?"] * len(wallet_ids))
        rows = db.fetchall(f"SELECT * FROM offlinelnurlw_link WHERE wallet IN ({q})", (*wallet_ids,))

    return [offlinelnurlwLink.from_row(row) for row in rows]


def update_offlinelnurlw_link(link_id: str, **kwargs) -> Optional[offlinelnurlwLink]:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    with open_ext_db("offlinelnurlw") as db:
        db.execute(f"UPDATE offlinelnurlw_link SET {q} WHERE id = ?", (*kwargs.values(), link_id))
        row = db.fetchone("SELECT * FROM offlinelnurlw_link WHERE id = ?", (link_id,))

    return offlinelnurlwLink.from_row(row) if row else None


def delete_offlinelnurlw_link(link_id: str) -> None:
    with open_ext_db("offlinelnurlw") as db:
        db.execute("DELETE FROM offlinelnurlw_link WHERE id = ?", (link_id,))