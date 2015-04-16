import boto.sqs
from boto.sqs.message import Message
conn = boto.sqs.connect_to_region("us-west-2",aws_access_key_id='AKIAJLHKOR7Z5KBGNH2Q',aws_secret_access_key='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')
q = conn.create_queue('myqueue')

m = Message()

m.set_body("hi")
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
print "these are all queues: " 
print conn.get_all_queues()
print "writing to queue"
q.write(m)

print "getting queue messgae"

rs = q.get_messages(message_attributes=['name1', 'name2'])
ma= rs[0].message_attributes['name1']['data_type']
print "len(rs_attrs)"
print len(rs)

print "----"
print rs[0].get_body()
print rs[0].message_attributes['name1']['string_value']
print "these are all messages:"
