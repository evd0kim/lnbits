from datetime import datetime
from quart import g, jsonify, request
from http import HTTPStatus
from lnurl.exceptions import InvalidUrl as LnurlInvalidUrl
import shortuuid  # type: ignore


from lnbits.core.crud import get_user
from lnbits.core.services import pay_invoice
from lnbits.decorators import api_check_wallet_key, api_validate_post_request

from lnbits.extensions.offlinelnurlw import offlinelnurlw_ext
from .crud import (
    create_offlinelnurlw_link,
    get_offlinelnurlw_link,
    get_offlinelnurlw_links,
    update_offlinelnurlw_link,
    delete_offlinelnurlw_link,
)


@offlinelnurlw_ext.route("/api/v1/links", methods=["GET"])
@api_check_wallet_key("invoice")
async def api_links():
    wallet_ids = [g.wallet.id]

    if "all_wallets" in request.args:
        wallet_ids = get_user(g.wallet.user).wallet_ids
    try:
        return (
            jsonify([{**link._asdict()} for link in get_offlinelnurlw_links(wallet_ids)]),
            HTTPStatus.OK,
        )
    except LnurlInvalidUrl:
        return (
            jsonify({"message": "LNURLs need to be delivered over a publically accessible `https` domain or Tor."}),
            HTTPStatus.UPGRADE_REQUIRED,
        )


@offlinelnurlw_ext.route("/api/v1/links/<link_id>", methods=["GET"])
@api_check_wallet_key("invoice")
async def api_link_retrieve(link_id):
    link = get_offlinelnurlw_link(link_id, 0)

    if not link:
        return jsonify({"message": "offlinelnurlw link does not exist."}), HTTPStatus.NOT_FOUND

    if link.wallet != g.wallet.id:
        return jsonify({"message": "Not your offlinelnurlw link."}), HTTPStatus.FORBIDDEN

    return jsonify({**link._asdict()}), HTTPStatus.OK


@offlinelnurlw_ext.route("/api/v1/links", methods=["POST"])
@api_check_wallet_key("admin")
@api_validate_post_request(
    schema={
        "title": {"type": "string", "empty": False, "required": True}
    }
)
async def api_link_create(link_id=None):

    link = create_offlinelnurlw_link(wallet_id=g.wallet.id, title=g.data['title'])
    return jsonify({**link._asdict()}), HTTPStatus.OK if link_id else HTTPStatus.CREATED


@offlinelnurlw_ext.route("/api/v1/links/<link_id>", methods=["DELETE"])
@api_check_wallet_key("admin")
async def api_link_delete(link_id):
    link = get_offlinelnurlw_link(link_id)

    if not link:
        return jsonify({"message": "offlineLNURLw link does not exist."}), HTTPStatus.NOT_FOUND

    if link.wallet != g.wallet.id:
        return jsonify({"message": "Not your offlineLNURLw link."}), HTTPStatus.FORBIDDEN

    delete_offlinelnurlw_link(link_id)

    return "", HTTPStatus.NO_CONTENT


# FOR LNURLs WHICH ARE NOT UNIQUE


@offlinelnurlw_ext.route("/api/v1/lnurl/<unique_hash>", methods=["GET"])
async def api_lnurl_response(unique_hash):
    link = get_offlinelnurlw_link_by_hash(unique_hash)

    if not link:
        return jsonify({"status": "ERROR", "reason": "LNURL-offlinelnurlw not found."}), HTTPStatus.OK

    if link.is_unique == 1:
        return jsonify({"status": "ERROR", "reason": "LNURL-offlinelnurlw not found."}), HTTPStatus.OK
    usescsv = ""
    for x in range(1, link.uses - link.used):
        usescsv += "," + str(1)
    usescsv = usescsv[1:]
    link = update_offlinelnurlw_link(link.id, used=link.used + 1, usescsv=usescsv)

    return jsonify(link.lnurl_response.dict()), HTTPStatus.OK


# FOR LNURLs WHICH ARE UNIQUE


@offlinelnurlw_ext.route("/api/v1/lnurl/<unique_hash>/<id_unique_hash>", methods=["GET"])
async def api_lnurl_multi_response(unique_hash, id_unique_hash):
    link = get_offlinelnurlw_link_by_hash(unique_hash)

    if not link:
        return jsonify({"status": "ERROR", "reason": "LNURL-offlinelnurlw not found."}), HTTPStatus.OK
    useslist = link.usescsv.split(",")
    usescsv = ""
    found = False
    if link.is_unique == 0:
        for x in range(link.uses - link.used):
            usescsv += "," + str(1)
    else:
        for x in useslist:
            tohash = link.id + link.unique_hash + str(x)
            if id_unique_hash == shortuuid.uuid(name=tohash):
                found = True
            else:
                usescsv += "," + x
    if not found:
        return jsonify({"status": "ERROR", "reason": "LNURL-offlinelnurlw not found."}), HTTPStatus.OK

    usescsv = usescsv[1:]
    link = update_offlinelnurlw_link(link.id, used=link.used + 1, usescsv=usescsv)
    return jsonify(link.lnurl_response.dict()), HTTPStatus.OK


@offlinelnurlw_ext.route("/api/v1/lnurl/cb/<unique_hash>", methods=["GET"])
async def api_lnurl_callback(unique_hash):
    link = get_offlinelnurlw_link_by_hash(unique_hash)
    k1 = request.args.get("k1", type=str)
    payment_request = request.args.get("pr", type=str)
    now = int(datetime.now().timestamp())

    if not link:
        return jsonify({"status": "ERROR", "reason": "LNURL-offlinelnurlw not found."}), HTTPStatus.OK

    if link.is_spent:
        return jsonify({"status": "ERROR", "reason": "offlinelnurlw is spent."}), HTTPStatus.OK

    if link.k1 != k1:
        return jsonify({"status": "ERROR", "reason": "Bad request."}), HTTPStatus.OK

    if now < link.open_time:
        return jsonify({"status": "ERROR", "reason": f"Wait {link.open_time - now} seconds."}), HTTPStatus.OK

    try:
        pay_invoice(
            wallet_id=link.wallet,
            payment_request=payment_request,
            max_sat=link.max_offlinelnurlwable,
            extra={"tag": "offlinelnurlw"},
        )

        changes = {
            "open_time": link.wait_time + now,
        }

        update_offlinelnurlw_link(link.id, **changes)
    except ValueError as e:
        return jsonify({"status": "ERROR", "reason": str(e)}), HTTPStatus.OK
    except PermissionError:
        return jsonify({"status": "ERROR", "reason": "offlinelnurlw link is empty."}), HTTPStatus.OK
    except Exception as e:
        return jsonify({"status": "ERROR", "reason": str(e)}), HTTPStatus.OK

    return jsonify({"status": "OK"}), HTTPStatus.OK
