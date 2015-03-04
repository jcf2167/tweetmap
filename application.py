from flask import Flask, render_template, request, redirect, g 
import tweepy
import json
import sqlite3
import threading
import time 
#from flaskext.mysql import MySQL



print "working"

DATABASE = 'coord.db'
app = Flask(__name__)
conn = sqlite3.connect("coord.db")
cursor = conn.cursor()
SQLITE_THREADSAFE = 2

fake_db=[]
# Authentication details. To  obtain these visit dev.twitter.com
consumer_key = 'rWBeqBjr3v9KbHeKwFr30FcT4'
consumer_secret = 'HKThlcphUISUkfr7pszy8adme9L9GvkZgON6MsjOQl2FSuWasq'
access_token = '431061070-SxikicdfSCuVg763C8ON7QgbGrTxsIT08lhCM1EJ'
access_token_secret = 'I28gbPCpNbHeUs0LEc7x2pX5hTjoTTFe1nqhxTxwYCTZC'

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

#--------END DATABASE STUFF----------------

# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener,):
    def __init__(self, keyword,number_tweets):
        self.num_tweets= 0
        print "HERE SHITHEADS"
        self.max_tweets= int(number_tweets)
        print self.max_tweets
        self.key = keyword

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
            
                location = decoded['user']['location']
                self.num_tweets = self.num_tweets + 1
                print "compareiosn:"
                print self.num_tweets
                print self.max_tweets
                if self.num_tweets < self.max_tweets:
                    
                    print "geolocation: "
                    print geolocation
                    print "location"
                    print location
                    #cursor.execute('insert into loc (user, lat, long) values (?, ?, ?);',
                    #[keyword,geolocation[0],geolocation[1]])
                    info = [self.key,geolocation[0],geolocation[1]]
                    fake_db.append(info)
                    print fake_db
                    print info
                    print self.num_tweets
                    print '_________________________________________'
                    return True
                else:
                    return False
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
    l = StdOutListener(keyword, number_tweets)
    stream = tweepy.Stream(auth, l)
    stream.filter(track=keyword)



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
    number_tweets = request.form['number_tweets']
    print number_tweets
    print keyword
    #__________Using keyword to find a list of streaming tweets w that keyword_____
    #initialization 
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    #st = threading.Thread(target=stream_tweet, args=[keyword])
    #print st
    #st.start()
    print "debug0"
    #exam = cursor.execute("select * from loc;")
    #entires = exam.fetchall()
    print "debug1   "
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    print "start streaming"
    l = StdOutListener(keyword,number_tweets)

    stream = tweepy.Stream(auth, l)
    stream.filter(track=keyword)

    print "Showing all new tweets for #programming:"
    return redirect('/showmap/'+keyword+"/"+number_tweets)

@app.route('/showmap/<keyword>/<number_tweets>')
def showmap(keyword,number_tweets):
    print " _________________________________________showmap____"
    
    print fake_db
    '''
    pass_db = []
    for x in fake_db:
        cursor.execute('insert into loc (user, lat, long) values (?, ?, ?);', [x[0], x[1], x[2]])
        if x[0]==keyword:
            pass_db.append[x]
        fake_db.remove(x)

    '''
    print "fake db"
    print fake_db
    print keyword
    return render_template('map.html',keyword=keyword, db=fake_db)

@app.route('/')
def hi(keyword):
    author = "Me"
    name = "You"
    return render_template('index.html', author=author, name=name)
  

if __name__ == '__main__':
    app.run()
    '''
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    print "Showing all new tweets for #programming:"
    stream = tweepy.Stream(auth, l)
    stream.filter(locations=[-122.75,36.8,-121.75,37.8])
    '''

    
