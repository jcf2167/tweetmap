from __future__ import absolute_import, print_function

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream


consumer_key = 'rWBeqBjr3v9KbHeKwFr30FcT4'

consumer_secret = 'HKThlcphUISUkfr7pszy8adme9L9GvkZgON6MsjOQl2FSuWasq'
access_token = '431061070-SxikicdfSCuVg763C8ON7QgbGrTxsIT08lhCM1EJ'
access_token_secret = 'I28gbPCpNbHeUs0LEc7x2pX5hTjoTTFe1nqhxTxwYCTZC'
class StdOutListener(StreamListener):

    """ A listener handles tweets are the received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def on_data(self, data):
        print(data)
        return True

    def on_error(self, status):
        print(status)

if __name__ == '__main__':
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    stream = Stream(auth, l)
    stream.filter(locations=[-179.9,-89.9,179.9,89.9])
