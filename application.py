from flask import Flask, render_template, request, redirect, g 
import tweepy
import json
import sqlite3
import threading
import time 
import mysql.connector
import threading 
from threading import Thread
import boto.sns
from requests import get as rget
import urllib2

from alchemyapi import AlchemyAPI
import boto.sqs
from boto.sqs.message import Message

from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit

DATABASE = 'coord.db'
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

db=[]

alchemyapi = AlchemyAPI()

sentimentdb = []

with open("config") as f:
    content = f.readlines()
consumer_key = content[0].rstrip()
consumer_secret = content[1].rstrip()
access_token = content[2].rstrip()
access_token_secret = content[3].rstrip()

conn = boto.sqs.connect_to_region("us-west-2")
queue_sns = conn.create_queue('cloudcomp')
queue_sns_sentiment = conn.create_queue('sentimentcloud')
c = boto.sns.connect_to_region("us-west-2")
topicname = "cloudcomp"
topicarn = c.create_topic(topicname)

config = {
  'user': 'jessicafan',
  'password': 'jessicafan',
  'host': 'cloud.c1xwtu16srrr.us-east-1.rds.amazonaws.com',
  'database': 'cloud',
  'raise_on_warnings': True,
}

#------------DATABASE STUFF----------------


class StdOutListener(tweepy.StreamListener,):

    def __init__(self):
        self.max=100000

    def on_data(self, data):
        decoded = json.loads(data)
        #print decoded
        if 'user' in decoded:
            # Also, we convert UTF-8 to ASCII ignoring all bad characters sent by users
            #print '@%s: %s' % (decoded['user']['screen_name'], decoded['text'].encode('ascii', 'ignore'))
            user = decoded['user']['screen_name']
            text = decoded['text'].encode('ascii', 'ignore')
            if decoded["geo"] == None:
                pass
            else:
                geolocation = decoded['geo']['coordinates']
                tweet_id = decoded['id_str'].encode('ascii')
                location = decoded['user']['location']
                lat= geolocation[0]
                lng = geolocation[1]
                cnx = mysql.connector.connect(**config)
                cursor = cnx.cursor()
                test = ("INSERT INTO tweet "
                    "(keyword, lat, lng, tweet, tweet_id) "
                    "VALUES (%s, %s, %s, %s, %s)")
            
                data_one = (user,lat,lng,text,tweet_id)
                cursor.execute(test, data_one)
                cnx.commit()
                cursor.close()
        return True

    def on_error(self, status):
        print status

@app.route('/more')
def more():
    keyword = request.args.get('keyword')
    posCount =  request.args.get('posCount')
    negCount = request.args.get('negCount')
    return render_template('analyze.html', keyword=keyword, 
                                           posCount=posCount, 
                                           negCount=negCount)


@app.route('/subscribe', methods=['POST','GET'])
def subscribe():
    headers = request.headers
    obj = json.loads(request.data)  
    header_type = headers.get('X-Amz-Sns-Message-Type')
    if header_type == "SubscriptionConfirmation":
        obj = json.loads(request.data)
        subscribe_url = obj[u'SubscribeURL']
        r = rget(subscribe_url)
        print "subscription confirmed"
    elif header_type == "Notification":
        if 'Subject' in obj:
            msg = obj[u'Message']
            body = obj[u'Subject']
            body = body.split("|")
            lat = body[0]
            lng = body[1]
            time = body[2]
            sentiment = body[3]
            socketio.emit('my response',
                      {'data': 'Server generated event',
                        'lat':lat,
                        'lng': lng,
                        'sentiment': sentiment
                      },
                      namespace='/test')
    return '', 200

@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1

@app.route('/')
def hello_world(): 
    author = "Me"
    name = "You"
    return render_template('index.html', author=author, name=name)

@app.route('/compute', methods = ['POST'])
def signup():
    keyword = request.form['keyword']
    print("Finding keyword " + keyword + " ")
    sentimentdb[:]=[]
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    query = "SELECT lat, lng, tweet FROM tweet WHERE tweet LIKE \"%" + keyword +"%\""
    cursor.execute(query)
    #queue_sns.purge()
    
    db = []
    for (lat, lng, tweet) in cursor:
        db.append([tweet,lat, lng])
        m=Message()
        body = str(lat)+"|"+str(lng)+"|"+str(tweet)+"|"+str(time.strftime("%b %d %Y %H:%M:%S", time.gmtime()))
        m.set_body(body) 
        queue_sns.write(m)
    print "============push into html========================================="
    cursor.close()
    cnx.close()
    return redirect('/showmap/'+keyword)

@app.route('/showmap/<keyword>')
def showmap(keyword):

    return render_template('map.html',keyword=keyword, db=sentimentdb)


def start_stream():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
    auth.set_access_token(access_token, access_token_secret)
    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.filter(locations=[-179.9,-89.9,179.9,89.9])

def startworker1():
    #running forever 
    while True:
        msg = queue_sns.get_messages()
        msgjson={}
        while(len(msg)>0):
            body_str = msg[0].get_body()
            queue_sns.delete_message(msg[0])
            body = body_str.split("|")
            lat = body[0]
            msgjson["lat"]=lat  
            lng = body[1]
            msgjson["lng"] = lng    
            tweet = body[2]
            msgjson["tweet"] =tweet     
            time = body[3]
            msgjson["time"]=time   
            response = alchemyapi.sentiment("text", tweet)
            m = Message()
            if 'docSentiment' not in response:
                print "docSentiment not in reponse"
                response = "neutral"
            else:
                response = response["docSentiment"]["type"]
            msgjson["sentiment"]=response
            added_sentiment = body_str +"|"+ response
            m.set_body(added_sentiment)
            msg = queue_sns.get_messages()
            json_data = json.dumps(msgjson)
            topicarn="arn:aws:sns:us-west-2:708326387433:cloudcomp"
            tempstr = lat+"|"+lng+"|"+time+"|"+response
            added_sentiment = added_sentiment.encode("utf8")
            tempstr=tempstr.encode("utf8")
            publication = c.publish(topicarn, message=tweet,  subject=tempstr)


def runThread():
    #st = threading.Thread( target = start_stream ) #start thread at very beginning 
    worker1 = threading.Thread(target= startworker1)
    #st.start()
    worker1.start()


if __name__ == '__main__':
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    app.before_first_request(runThread)
    socketio.run(app, host='0.0.0.0', port=5004)


