from flask import Flask, render_template, request, redirect, g 
import tweepy
import json
import sqlite3
import threading
import time 
import mysql.connector
import threading 
import boto.sqs
from boto.sqs.message import Message

#from flaskext.mysql import MySQL

print "working"

DATABASE = 'coord.db'
app = Flask(__name__)
conn = sqlite3.connect("coord.db")
cursor = conn.cursor()
SQLITE_THREADSAFE = 2

fake_db=[]
# Authentication details. To  obtain these visit dev.twitter.com
with open("config") as f:
    content = f.readlines()
consumer_key = content[0].rstrip()
consumer_secret = content[1].rstrip()
access_token = content[2].rstrip()
access_token_secret = content[3].rstrip()

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

def connect_sqs():
    conn = boto.sqs.connect_to_region("us-west-2",aws_access_key_id=content[4].rstrip(),aws_secret_access_key=content[5].rstrip())
    q = conn.create_queue('myqueue')
    print q
    m = Message()
    m.set_body('This is my first message.')
    print "these are all queues: "
    print conn.get_all_queues()
    q.write(m)
    rs = q.get_messages()
    m = rs[0]
    print m.get_body()
    q.delete_message(m)
    print q


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
                print location
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



@app.route('/')
def hello_world():
    
    author = "Me"
    name = "You"
    return render_template('index.html', author=author, name=name)


@app.route('/compute', methods = ['POST'])
def signup():
    print " _________________________________________COMPUTE____"
    keyword = request.form['keyword']
    print("Finding keyword " + keyword + " ")

    print keyword
    #__________Using keyword to find a list of streaming tweets w that keyword_____
    #initialization 
    print "Showing all new tweets for #programming:"
    return redirect('/showmap/'+keyword)

@app.route('/showmap/<keyword>')
def showmap(keyword):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    query = "SELECT lat, lng, tweet FROM tweet WHERE tweet LIKE \"%" + keyword +"%\""

    print "cursor is excuging"
    cursor.execute(query)
    print "done:"

    db = []
    for (lat, lng, tweet) in cursor:
        db.append([tweet,lat, lng])
    print len(db)
    cursor.close()
    cnx.close()
    '''
    pass_db = []
    for x in fake_db:
        cursor.execute('insert into loc (user, lat, long) values (?, ?, ?);', [x[0], x[1], x[2]])
        if x[0]==keyword:
            pass_db.append[x]
        fake_db.remove(x)
    '''
    print "fake db"

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


def runThread():
    st = threading.Thread( target = start_stream )
    st.start()

if __name__ == '__main__':
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    print cnx
    #app.run(host='0.0.0.0')
    app.before_first_request(runThread)
    connect_sqs()
    app.run()
    

    