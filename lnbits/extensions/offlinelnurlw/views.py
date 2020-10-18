from quart import g, abort, render_template
from http import HTTPStatus

from lnbits.decorators import check_user_exists, validate_uuids

from lnbits.extensions.offlinelnurlw import offlinelnurlw_ext


@offlinelnurlw_ext.route("/")
@validate_uuids(["usr"], required=True)
@check_user_exists()
async def index():
    return await render_template("offlinelnurlw/index.html", user=g.user)
