import boto.sqs
from boto.sqs.message import Message
conn = boto.sqs.connect_to_region("us-west-2")
q = conn.create_queue('myqueue')
'''
m = Message()
m_copy = Message()
m.set_body("hi")
m_copy.set_body("hi1")
m.message_attributes = {
    "name1": {
        "data_type": "String",
        "string_value": "I am a string"
    },
    "name2": {
        "data_type": "Number",
        "string_value": "12"
    }
}
m_copy.message_attributes = {
    "name1": {
        "data_type": "String",
        "string_value": "I am a string!!!!!!"
    },
    "name2": {
        "data_type": "Number",
        "string_value": "12"
    }
}
print "these are all queues: " 
print conn.get_all_queues()
print "writing to queue"
q.write(m)
q.write(m_copy)
'''
print "getting queue messgae"
rs = q.get_messages(message_attributes=['name1', 'name2'])
while(len(rs)>0):
	print len(rs)
#	print rs[0].get_body()
	print rs[0].message_attributes['name1']['string_value']
	rs = q.get_messages(message_attributes=['name1', 'name2'])
	

print "len(rs_attrs)"
print len(rs)

print "----"
print "these are all messages:"
