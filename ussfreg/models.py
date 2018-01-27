from django.db import models
from django.utils import timezone
from django_countries.fields import CountryField
import jsonfield
from django.utils.translation import ugettext_lazy as _
from localflavor.us.models import USStateField
import json
#from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.


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
            
    def ussf_to_json(self):
        address = { 
            "street_1": self.address1,
            "street_2": self.address2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.zipcode,
            "country_code": "US"
        }

        submission = { 
            "name_first": self.first_name,
            "name_last": self.last_name,
            "email": "%s.%s@gmail.com" % ( self.first_name, self.last_name),
            "gender": "male",
            "dob": "2008-08-22",
            "phone_number": "123-456-7890",
            "address": address,
            "citizenship": ["US"],
            "citizenship_country": "string",
            "played_outside_us": "no",
            "previous_club_country": "",
            "previous_club_name": "",
            "most_recent_school": "Elm Street Elementary",
            "external_id": self.id,
        }
        return json.dumps(submission)



class Competition(models.Model):
    name = models.CharField('competition', max_length=32)
    modtime = models.DateTimeField(auto_now=True)
    ussf_id = models.CharField('ussf-id', max_length=32, null=True, blank=True)
    ussf_submitted = models.DateTimeField(blank=True, null=True)

    @property
    def ussf_needs_update(self):
        return self.ussf_submitted is None or self.ussf_submitted < self.modtime

    def ussf_to_json(self):
        contact = {
            "name_first": "Joe",
            "name_last": "Smith",
            "role": "Apt 121",
            "email": "sam.smith@email.com",
            "phone_primary": "555-223-1234",
            "phone_secondary": "111-123-5678",
        }
        address = {
            "street_1": "99999 Main St.",
            "street_2": "Suite 121",
            "city": "Nashua",
            "state": "NH",
            "postal_code": "03060",
            "country_code": "US",
        }
        submission = {
            "name": self.name,
            "type": "club",
            "ages": "u-12",
            "gender": "co-ed",
            "contact": contact,
            "address": address,
            "external_id": self.id
        }
        return json.dumps(submission)

