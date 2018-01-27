from django.shortcuts import render

# Create your views here.

import base64, copy, json, datetime, hashlib, hmac, logging
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import WebhookMessage
from .tasks import ProcessIncoming



logger = logging.getLogger(__name__)
APIKEY = settings.USSF_API_KEY


def process_message(request, hook):
    jsondata = request.body
    data = json.loads(jsondata)
    meta = copy.copy(request.META)

    for k, v in meta.items():
        if not isinstance(v, basestring):
            del meta[k]

    for field in ['x-ussf-timestamp', 'Authorization']: 
        if field not in meta:
            logger.error("%s not found" % field)
            return False
    # validate
    payload = meta['x-ussf-timestamp'] + jsondata
    sig_calc = base64.b64encode(hmac.new(APIKEY, msg=payload, digestmode=hashlib.sha256).digest())
    if sig_calc != meta['Authorization']:
        logger.error("Authorization mismatch")
        return False

    obj = WebhookMessage.objects.create(
        date_event_generated=datetime.datetime.fromtimestamp(
            data['timestamp']/1000.0, 
            tz=timezone.get_current_timezone()
        ),
        body=data,
        request_meta=meta,
        hook = hook,
    )
    logger.info("Message %d accepted" % obj.id)
    return True

    

@csrf_exempt
@require_POST
def competition_callback(request):
    if process_message(request, WebhookMessage.COMPETITION):
        return HttpResponse("Success", status=200)
    else:
        return HttpResponse("Access Denied", status=403)


@csrf_exempt
@require_POST
def player_callback(request):
    if process_message(request, WebhookMessage.PLAYER):
        return HttpResponse("Success", status=200)
    else:
        return HttpResponse("Access Denied", status=403)


def kickit(request):
    logger.info("kicking it...")
    ProcessIncoming().run()
    return HttpResponse("Success", status=200)
    
