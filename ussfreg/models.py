import base64
import datetime
import hashlib
import hmac
import json
import jsonfield
import logging
import requests

from django.conf import settings
from django_countries.fields import CountryField
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from localflavor.us.models import USStateField


logger = logging.getLogger(__name__)
USSF_URL = settings.USSF_URL
APIKEY = settings.USSF_API_KEY
CLIENTID =  settings.USSF_CLIENT_ID

class WebhookMessage(models.Model):
    UNPROCESSED = 'U'
    PROCESSED = 'P'
    ERROR = 'E'

    STATUSES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

    COMPETITIONS = 'C'
    PLAYERS = 'P'
    WEBHOOKS = (
        (COMPETITIONS, "Competitions"),
        (PLAYERS, "Players"),
    )

    date_received = models.DateTimeField(default=timezone.now)
    hook = models.CharField(max_length=1, choices=WEBHOOKS)
    body = jsonfield.JSONField()
    request_meta = jsonfield.JSONField()
    status = models.CharField(max_length=1, choices=STATUSES,
                              default=UNPROCESSED)
    status_message = models.CharField(max_length=250, null=True)

    def __unicode__(self):
        return u'{0}'.format(self.date_event_generated)


GENDERS = ( ( 'm', _('male')) , ('f', _('female')) )



class Player(models.Model):

    first_name = models.CharField(_('First (Given) Name'), max_length=20)
    last_name = models.CharField(_('Last (Family) Name'), max_length=20)
    address1 = models.CharField(
        _('mailing address'),
        max_length=50,
        help_text=_('Street address or PO BOX. Your player passcard will be sent to this address.'),
    )
    address2 = models.CharField(
        _('mailing address line 2'),
        max_length=50,
        blank=True,
        help_text=_('Apt, Unit, PMB, Suite, Mailbox only.'),
    )
    city = models.CharField(_('City'), max_length=50)
    state = USStateField(_('State'), blank=True, null=True)
    zipcode = models.CharField(
        _('Zip Code'),
        max_length=10,
        help_text=_('xxxxx or xxxxx-xxxx'),
        blank=True,
        null=True,
    )
    mass_id = models.CharField(_('MASS ID Number'), max_length=20, blank=True)
    dob = models.DateField(_('Date of Birth'), help_text='mm/dd/yyyy')
    country = CountryField(_('Country of Birth'),
        help_text=(_("""Country of birth is required by US Soccer for
                        international clearance requirements by FIFA. The last item
                        in the list is 'Not Specified'. If you chose this
                        option, you might NOT be eligible to play in any national amateur or international
                        competitions."""))
    )
    gender = models.CharField(_('gender'),max_length=1, choices=GENDERS )
    underProContract = models.BooleanField('Under Profesional Contract', default=False,
        help_text=_('Please check if you are under a professional soccer contract'))
    modtime = models.DateTimeField(auto_now=True)
    ussf_id = models.CharField('ussf-id', max_length=32, null=True, blank=True)
    ussf_submitted = models.DateTimeField(blank=True, null=True)

    @property
    def ussf_needs_update(self):
        return self.ussf_submitted is None or self.ussf_submitted < self.modtime
            
    def ussf_to_json(self, comp):
        address = { 
            "street_1": self.address1,
            "street_2": self.address2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.zipcode,
            "country_code": "US"
        }

        competition = {
            "fifa_id": comp.fifa_id,
        }

        submission = { 
            "name_first": self.first_name,
            "name_last": self.last_name,
            "email": "%s.%s@gmail.com" % ( self.first_name, self.last_name),
            "gender": "male",
            "dob": "1961-02-02",
            "type": "reg",
            "level": "Amateur",
            "date_start": "2018-02-20",
            "date_end": "2019-12-31",
            "phone_number": "123-456-7890",
            "address": address,
            "citizenship": ["US"],
            "played_outside_us": False,
            "previous_club_country": "",
            "previous_club_name": "",
            "most_recent_school": "Elm Street Elementary",
            "external_id": self.id,
            "state_member": "Massachusetts Adult State Soccer Association",
            "competiion": competition,
        }
        return json.dumps(submission)

    def send_to_ussf(self, comp):
        if self.ussf_needs_update:
            logger.info("sending player %d" % self.id)
            if xmit_to_ussf("registrations", self.ussf_to_json(comp)):
                self.ussf_submitted = datetime.datetime.now()
                self.save()



class Competition(models.Model):
    name = models.CharField('competition', max_length=32)
    modtime = models.DateTimeField(auto_now=True)
    ussf_id = models.CharField('ussf-id', max_length=32, null=True, blank=True)
    fifa_id = models.CharField('fifa-id', max_length=32, null=True, blank=True)
    ussf_submitted = models.DateTimeField(blank=True, null=True)

    @property
    def ussf_needs_update(self):
        return self.ussf_submitted is None or self.ussf_submitted < self.modtime

    def ussf_to_json(self):
        contact = {
            "name": "Joe Smith",
            "role": "admin",
            "email": "sam.smith@email.com",
            "phone_primary": "555-223-1234",
            "phone_secondary": "111-123-5678",
        }
        address = {
            "street_1": "99999 Main St.",
            "city": "Nashua",
            "state": "NH",
            "postal_code": "03060",
            "country_code": "US",
        }
        submission = {
            "name": self.name,
            "type": "league",
            "ages": "open",
            "gender": "co-ed",
            "contact": contact,
            "address": address,
            "external_id": self.id
        }
        return json.dumps(submission)

    def send_to_ussf(self):
        if self.ussf_needs_update:
            logger.info("sending comp %d" % self.id)
            if xmit_to_ussf("competitions", self.ussf_to_json()):
                self.ussf_submitted = datetime.datetime.now()
                self.save()
            else:
                logger.error("submission of competition %d failed" % self.id)



def xmit_to_ussf(api, json):
                logger.debug("json: " + json)
                path = USSF_URL + "/api/" + api
                logger.debug("path: " + path)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                logger.debug("timestamp: " + timestamp)
                payload = timestamp + json
                HMAC = hmac.new(APIKEY.encode(), msg=payload.encode(), digestmod=hashlib.sha256)
                sig_calc = base64.b64encode(HMAC.digest())
                auth = "ussf {clientId}:{sig}".format(
                    clientId = CLIENTID,
                    sig=sig_calc.decode(),
                )
                logger.debug("AUTH: " + auth)
                headers = { 
                    'Authorization': auth, 
                    'x-ussf-timestamp': timestamp,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                }
                r = requests.post(path, headers=headers, data=json)
                logger.debug("RESPONSE TEXT: " + r.text)
                logger.debug("RESPONSE status code: %d" % r.status_code)
                return r.status_code == 202
                    
