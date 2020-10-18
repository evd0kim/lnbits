from quart import Blueprint


offlinelnurlw_ext: Blueprint = Blueprint("offlinelnurlw", __name__, static_folder="static", template_folder="templates")


from .views_api import *  # noqa
from .views import *  # noqa
