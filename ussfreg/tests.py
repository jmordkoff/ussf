from django.test import TestCase
from django.test.client import Client
import simplejson



# wget -O - -q --post-file sample.json --header='x-ussf-timestamp:12234'  --header='authorization:foo' http://reg.mass-soccer.org:8888/webhook/player


class TestPipeline(TestCase):


    def test_your_test(self):
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

                         



