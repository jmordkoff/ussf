from django.shortcuts import render

# Create your views here.

import base64, copy, json, datetime, hashlib, hmac, logging
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import WebhookMessage
from .tasks import ProcessIncoming, ProcessOutgoing



logger = logging.getLogger(__name__)
APIKEY = settings.USSF_API_KEY


def process_message(request, hook):
    jsondata = request.body.decode()
    data = json.loads(jsondata)
    meta_in = copy.copy(request.META)

    meta = {k: v for k, v in meta_in.items() if isinstance(v, str)}
    for k,v in meta.items():
        print("meta: \"%s\" = \"%s\"" % (k, v))

    for field in ['HTTP_X_USSF_TIMESTAMP', 'HTTP_AUTHORIZATION' ]:
        if field not in meta:
            logger.error("%s not found" % field)
            return False
    # validate
    payload = meta['HTTP_X_USSF_TIMESTAMP'] + jsondata
    sig_calc = base64.b64encode(hmac.new(str.encode(APIKEY), msg=str.encode(payload), digestmod=hashlib.sha256).digest())
    if sig_calc != meta['HTTP_AUTHORIZATION']:
        logger.error("Authorization mismatch")
        #return False

    obj = WebhookMessage.objects.create(
        body=data,
        request_meta=meta,
        hook = hook,
    )
    logger.info("Message %d accepted" % obj.id)
    return True

    

@csrf_exempt
@require_POST
def competition_callback(request):
    if process_message(request, WebhookMessage.COMPETITIONS):
        return HttpResponse("Success", status=200)
    else:
        return HttpResponse("Access Denied", status=403)


@csrf_exempt
@require_POST
def player_callback(request):
    if process_message(request, WebhookMessage.PLAYERS):
        return HttpResponse("Success", status=200)
    else:
        return HttpResponse("Access Denied", status=403)


def kickit(request):
    logger.info("kicking it...")
    ProcessIncoming().run()
    ProcessOutgoing().run()
    return HttpResponse("Success", status=200)
    
