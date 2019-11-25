# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client
import secrets

# Your Account Sid and Auth Token from twilio.com/console
# DANGER! This is insecure. See http://twil.io/secure
account_sid = 'AC22984e41ab644fd7eb761fca7a3c4682'
auth_token = '3327af0a7681f8183a4805964d6e9923'
client = Client(account_sid, auth_token)

message = client.messages \
                .create(
                     body="Join Earth's mightiest heroes. Like Kevin Bacon.",
                     from_='+13037316323',
                     to='+14153751320'
                 )

print(message.sid)
