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

#from flaskext.mysql import MySQL

print "working"

DATABASE = 'coord.db'
app = Flask(__name__)
alchemyapi = AlchemyAPI()

sentimentdb = []
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
my_ip = urllib2.urlopen('http://ip.42.pl/raw').read()


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
    print "_____________________"
    obj = json.loads(request.data)
    #print obj

    
    header_type = headers.get('X-Amz-Sns-Message-Type')
    if header_type == "SubscriptionConfirmation":
        print "yes!"
        obj = json.loads(request.data)
        subscribe_url = obj[u'SubscribeURL']
        print "subscribe_url!!"
        print subscribe_url
        print "_____________________ end SUBSCRIPTION___________________"
        r = rget(subscribe_url)
        
        print "subscription confirmd"
    elif header_type == "Notification":
        print "NOTIVARTION"
        #print request.body
        print obj
        print obj[u'Timestamp']
        if 'Subject' in obj:
            print "message is in obj"
            msg = obj[u'Message']
            print msg
            body = obj[u'Subject']
            body = body.split("|")
            print "this is the body array"
            print body
            lat = body[0]
            print lat
            #print "lat " + lat
            lng = body[1]
            print lng
            #print "tweet " + tweet
            time = body[2]
            print time
            sentiment = body[3]
            print sentiment
            datapoint = [msg, lat,lng, time, sentiment]
            sentimentdb.append(datapoint)


    return '', 200


@app.route('/')
def hello_world(): 
    author = "Me"
    name = "You"
    return render_template('index.html', author=author, name=name)

def trythis():
    ip="http://"+my_ip+":5005/subscribe"
    subscription = c.subscribe("arn:aws:sns:us-west-2:708326387433:cloudcomp", "http", ip)
    print "subscription: "
    print subscription

    r=rget(ip)

    if r.status_code == 200:
        print "we're good"
    else:
        print r.status_code

@app.route('/compute', methods = ['POST'])
def signup():
    keyword = request.form['keyword']
    print("Finding keyword " + keyword + " ")
    sentimentdb[:]=[]
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
    cursor.close()
    cnx.close()
    return redirect('/showmap/'+keyword)

@app.route('/showmap/<keyword>')
def showmap(keyword):
    print len(sentimentdb)
    return render_template('map.html',keyword=keyword, db=sentimentdb)



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
        msgjson={}
        #print len(msg)
        #print type(msg)
        while(len(msg)>0):
            body_str = msg[0].get_body()
            queue_sns.delete_message(msg[0])
            #print body_str
            body = body_str.split("|")
            lat = body[0]
            msgjson["lat"]=lat
            #print "lat " + lat
            lng = body[1]
            msgjson["lng"] = lng
            #print "lng " + lng
            tweet = body[2]
            msgjson["tweet"] =tweet
            #print "tweet " + tweet
            time = body[3]
            msgjson["time"]=time
            #print "time " + time
            response = alchemyapi.sentiment("text", tweet)
            m = Message()
            if 'docSentiment' not in response:
                response = "neutral"
            else:
                response = response["docSentiment"]["type"]

            msgjson["sentiment"]=response
            added_sentiment = body_str +"|"+ response
            #print "new Body: " + added_sentiment
            m.set_body(added_sentiment)
            #queue_sns_sentiment.write(m)

            msg = queue_sns.get_messages()
            json_data = json.dumps(msgjson)
            topicarn="arn:aws:sns:us-west-2:708326387433:cloudcomp"
            print "about to publish"
            print str(added_sentiment)
            tempstr = lat+"|"+lng+"|"+time+"|"+response
            print "Type tempstr"
            print tempstr
            added_sentiment = added_sentiment.encode("utf8")
            print type(added_sentiment)
            tempstr=tempstr.encode("utf8")
            publication = c.publish(topicarn, message=tweet,  subject=tempstr)


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


    
