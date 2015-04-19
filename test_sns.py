import boto.sns
import urllib2
from requests import get as rget
c = boto.sns.connect_to_region("us-west-2")
my_ip = urllib2.urlopen('http://ip.42.pl/raw').read()

topicname = "cloudcomp"
topicarn = c.create_topic(topicname)
ip="http://"+my_ip+":5005/subscribe"
subscription = c.subscribe("arn:aws:sns:us-west-2:708326387433:cloudcomp", "http", ip)
print "subscription: "
print subscription
r=rget(ip)
print r
if r.status_code == 200:
        print "we're good"
else:
	print "we're bad"
        print r.status_code
