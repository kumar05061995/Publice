import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant, ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_api_key_sid = os.environ.get('TWILIO_API_KEY_SID')
twilio_api_key_secret = os.environ.get('TWILIO_API_KEY_SECRET')



# twilio_account_sid = "ACa70d424aa1c5587feb493534cfec6da6"
# twilio_api_key_sid = "SK425775c4e23eb67824ee020fbdde408f"
# twilio_api_key_secret = "facoDxadkNgFln1Wwk5Dn3ih7QgVgLTL"


twilio_client = Client(twilio_api_key_sid, twilio_api_key_secret,
                       twilio_account_sid)


# TWILIO_ACCOUNT_SID = "ACa70d424aa1c5587feb493534cfec6da6"
# TWILIO_API_KEY_SID = "SK425775c4e23eb67824ee020fbdde408f"
# TWILIO_API_KEY_SECRET = "facoDxadkNgFln1Wwk5Dn3ih7QgVgLTL"

app = Flask(__name__)


def get_chatroom(name):
    for conversation in twilio_client.conversations.conversations.stream():
        if conversation.friendly_name == name:
            return conversation

    # a conversation with the given name does not exist ==> create a new one
    return twilio_client.conversations.conversations.create(
        friendly_name=name)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.get_json(force=True).get('username')
    if not username:
        abort(401)

    conversation = get_chatroom('My Room')
    try:
        conversation.participants.create(identity=username)
    except TwilioRestException as exc:
        # do not error if the user is already in the conversation
        if exc.status != 409:
            raise

    token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                        twilio_api_key_secret, identity=username)
    token.add_grant(VideoGrant(room='My Room'))
    token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

    return {'token': token.to_jwt(),
            'conversation_sid': conversation.sid}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
