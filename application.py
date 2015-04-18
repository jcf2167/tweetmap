from flask import Flask, render_template, request, redirect, g 
import tweepy
import json
import sqlite3
import threading
import time 
import mysql.connector
import threading 
import boto.sns
from requests import get as rget

from alchemyapi import AlchemyAPI
import boto.sqs
from boto.sqs.message import Message

#from flaskext.mysql import MySQL

print "working"

DATABASE = 'coord.db'
app = Flask(__name__)
alchemyapi = AlchemyAPI()

fake_db=[]

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

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

class StdOutListener(tweepy.StreamListener,):

    def __init__(self):
        self.max=100000

    def on_data(self, data):
        # Twitter returns data in JSON format - we need to decode it first
        decoded = json.loads(data)
        #print decoded
        if 'user' in decoded:
            # Also, we convert UTF-8 to ASCII ignoring all bad characters sent by users
            #print '@%s: %s' % (decoded['user']['screen_name'], decoded['text'].encode('ascii', 'ignore'))
            user = decoded['user']['screen_name']
            text = decoded['text'].encode('ascii', 'ignore')
           # print "________"
            #print text
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
               # print location
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

def stream_tweet(keyword):
    print "debug0"
    #exam = cursor.execute("select * from loc;")
    #entires = exam.fetchall()
    print "debug1   "
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    print "start streaming"
    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.filter()

@app.route('/subscribe', methods=['POST','GET'])
def subscribe():
    print "_____________________SUBSCRIPTION___________________"
    headers = request.headers
    print headers
    header_type = headers.get('X-Amz-Sns-Message-Type')
    if header_type == "SubscriptionConfirmation":
        print "yes!"
    obj = json.loads(request.data)


    return '', 200

@app.route('/')
def hello_world(): 
    '''
    ip="http://160.39.138.189/subscribe"
    subscription = c.subscribe("arn:aws:sns:us-west-2:708326387433:cloudcomp", "http", ip)
    print "subscription: "
    print subscription

    r=rget(ip)

    if r.status_code == 200:
        print "we're good"
    else:
        print r.status_code
    '''
    author = "Me"
    name = "You"
    return render_template('index.html', author=author, name=name)

@app.route('/compute', methods = ['POST'])
def signup():
    keyword = request.form['keyword']
    print("Finding keyword " + keyword + " ")
    return redirect('/showmap/'+keyword)

@app.route('/showmap/<keyword>')
def showmap(keyword):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    query = "SELECT lat, lng, tweet FROM tweet WHERE tweet LIKE \"%" + keyword +"%\""
    print "cursor is excuting: "
    cursor.execute(query)
    print "done:"

    #reads all database results into an array 
    #writes all database results into AWS SNS
    db = []
    for (lat, lng, tweet) in cursor:
        db.append([tweet,lat, lng])
        m=Message()
        body = str(lat)+"|"+str(lng)+"|"+str(tweet)+"|"+str(time.strftime("%b %d %Y %H:%M:%S", time.gmtime()))
        m.set_body(body) 
        queue_sns.write(m)

        '''
    #now we process tweets? 
    msg = queue_sns.get_messages()
    if len(msg)>0:
        body = msg[0].get_body()
        body = body.split("|")
        lat = body[0]
        lng = body[1]
        tweet = body[2]
        time = body[3]
        response = alchemyapi.sentiment("text", tweet)


    m = rs[0]
    print m.get_body()
                
    '''

    print len(db)
    cursor.close()
    cnx.close()

    return render_template('map.html',keyword=keyword, db=db)

@app.route('/')
def hi(keyword):
    author = "Me"
    name = "You"
    return render_template('index.html', author=author, name=name)

def start_stream():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
    auth.set_access_token(access_token, access_token_secret)
    print "dubug -1"
    l = StdOutListener()
    print "debug -2"
    stream = tweepy.Stream(auth, l)
    print "debug -3"
    #stream.filter(track="a")
    stream.filter(locations=[-179.9,-89.9,179.9,89.9])

def startworker1():
    #running forever 
    while True:
        msg = queue_sns.get_messages()
        #print len(msg)
        #print type(msg)
        while(len(msg)>0):
            body_str = msg[0].get_body()
            queue_sns.delete_message(msg[0])
            #print body_str
            body = body_str.split("|")
            lat = body[0]
            #print "lat " + lat
            lng = body[1]
            #print "lng " + lng
            tweet = body[2]
            #print "tweet " + tweet
            time = body[3]
            #print "time " + time
            response = alchemyapi.sentiment("text", tweet)
            m = Message()
            if 'docSentiment' not in response:
                response = "neutral"
            else:
                response = response["docSentiment"]["type"]

            added_sentiment = body_str +"|"+ response
            #print "new Body: " + added_sentiment
            m.set_body(added_sentiment)
            queue_sns_sentiment.write(m)
            msg = queue_sns.get_messages()


def runThread():
    st = threading.Thread( target = start_stream ) #start thread at very beginning 
    worker1 = threading.Thread(target= startworker1)
    st.start()
    worker1.start()

if __name__ == '__main__':
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    print cnx
    #app.run(host='0.0.0.0')

    app.before_first_request(runThread)
    print threading._active
    app.run(host='0.0.0.0',port=5005)


    
