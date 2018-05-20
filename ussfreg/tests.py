import datetime
import simplejson

from django.test import TestCase
from django.test.client import Client

from .models import Player



# wget -O - -q --post-file sample.json --header='x-ussf-timestamp:12234'  --header='authorization:foo' http://reg.mass-soccer.org:8888/webhook/player


class TestPipeline(TestCase):


    def test_player_webhook(self):
        python_dict = {
            "type": "player_registration",
            "request_url": "https://ussoccerconnect.com/api/registrations",
            "ussf_id": "9999-9999-9999-9999",
            "fifa_id": "1XXXXX3",
            "external_id": "1XXXXX3"
        }

        response = self.client.post('/webhook/player', 
                        simplejson.dumps(python_dict), 
                        content_type="application/json",
                        HTTP_X_USSF_TIMESTAMP="1234",
                        HTTP_AUTHORIZATION="foo"
                        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Success')
        # TODO verify the data is processable


    def createPlayer(self):
        pl = Player(
                first_name = 'joe',
                last_name = 'player',
                address1 = 'address1',
                city = 'Boston',
                state = 'MA',
                zipcode = '01234',
                mass_id = 'MA1800012345',
                dob = datetime.date(1961, 12, 12),
                country = 'US',
                gender = 'M',
            )
        pl.save()
        return pl
        
    def test_post_player(self):
        pl = self.createPlayer()
        pl.send_to_ussf()
        self.assertNotEqual(pl.ussf_submitted, None)

                         


