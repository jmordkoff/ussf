from celery.task import PeriodicTask
from celery.schedules import crontab
import logging
from django.conf import settings
from .models import Player, Competition, WebhookMessage

import base64, json, datetime, hashlib, hmac, logging, requests

logger = logging.getLogger(__name__)


USSF_URL = settings.USSF_URL
APIKEY = settings.USSF_API_KEY
CLIENTID =  settings.USSF_CLIENT_ID

class ProcessIncoming(PeriodicTask):
    run_every = crontab()

    def run(self):
        logger.info("Processing Incoming Messages")
        for message in WebhookMessage.objects.filter(status=WebhookMessage.UNPROCESSED):
            try:
                self.process_message(message)
                message.status = WebhookMessage.PROCESSED
                message.save()
            except Exception as e:
                message.status = WebhookMessage.ERROR
                message.status_message = str(e)
                message.save()

    def process_message(self, message):
        


        if message.hook == WebhookMessage.COMPETITION:
            self.process_competiion(message)
        elif message.hook == WebhookMessage.PLAYER:
            self.process_player(message)
        else:
            logger.error("unknown hook type %s in record %d" % ( message.hook, message.id))
            raise ValueError("bad hook code")

    def process_competion(self, message):
        pass
            
    def process_player(self, message):
        pass


class ProcessOutgoing(PeriodicTask):
    run_every = crontab()

    def run(self):
        logger.info("Processing Outgoing Messages")

        for comp in Competition.objects.all():
            if comp.ussf_needs_update:
                logger.info("sending comp %d" % comp.id)
                if self.send_to_ussf("competitions", comp.ussf_to_json()):
                    comp.ussf_submitted = datetime.datetime.now()
                    comp.save()


        for player in Player.objects.all():
            if player.ussf_needs_update:
                logger.info("sending player %d" % player.id)
                if self.send_to_ussf("registrations", player.ussf_to_json()):
                    player.ussf_submitted = datetime.datetime.now()
                    player.save()


    def send_to_ussf(self, api, json):
                path = USSF_URL + "/" + api
                logger.debug(path)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                logger.debug(timestamp)
                payload = timestamp + json
                logger.debug(json)
                HMAC = hmac.new(APIKEY.encode(), msg=payload.encode(), digestmod=hashlib.sha256)
                sig_calc = base64.b64encode(HMAC.digest())
                auth = "Authorization: ussf {clientId}:{sig}".format(
                    clientId = CLIENTID,
                    sig=sig_calc.decode(),
                )
                logger.debug(auth)
                headers = { 
                    'Authorization': auth, 
                    'x-ussf-timestamp': timestamp,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                }
                r = requests.post(path, headers=headers, data=json)    
                logger.debug(r.text)
                logger.debug(r.headers)
                return r.status_code == 200
                    

    


