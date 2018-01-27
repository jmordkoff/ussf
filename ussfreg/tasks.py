from celery.task import PeriodicTask
from celery.schedules import crontab

from .models import Player, Competition, WebhookMessage


class ProcessIncoming(PeriodicTask):
    run_every = crontab()

    def run(self):
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
        


        if message.hook = WebhookMessage.COMPETITION:
            self.process_competiion(message)
        elif message.hook = WebhookMessage.PLAYER:
            self.process_player(message)
        else:
            logger.error("unknown hook type %s in record %d" % ( message.hook, message.id))
            raise ValueError("bad hook code")

    def process_competion(self, message):
        pass
            
    def process_player(self, message):
        pass


