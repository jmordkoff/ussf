from celery.task import PeriodicTask
from celery.schedules import crontab
import logging
from .models import Player, Competition, WebhookMessage


logger = logging.getLogger(__name__)

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
        if message.hook == WebhookMessage.COMPETITIONS:
            self.process_competiion(message)
        elif message.hook == WebhookMessage.PLAYERS:
            self.process_player(message)
        else:
            logger.error("unknown hook type %s in record %d" % ( message.hook, message.id))
            raise ValueError("bad hook code")

    def process_competion(self, message):
        print("TODO - process competion")
            
    def process_player(self, message):
        print("TODO - process player")


class ProcessOutgoing(PeriodicTask):
    run_every = crontab()

    def run(self):
        logger.info("Processing Outgoing Messages")

        for comp in Competition.objects.all():
            comp.send_to_ussf()

        for player in Player.objects.all():
            player.set_to_ussf()

