#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 13:53:38 2024

@author: stanleyliu
"""
import json
import numpy
import os
from openai import OpenAI

file = open("sharc1-official/json/sharc_train.json")
data = json.load(file)

file = open("sharc1-official/json/sharc_test.json")
test_data = json.load(file)

sn = [i["snippet"]for i in data]
q = [i["answer"] for i in data]
l = [len(i) for i in sn]
N = 75

sn_test = [i["snippet"] for i in test_data]
q_test = [i["answer"] for i in test_data]

# sort snippets in decreasing length order
# z = numpy.array(range(len(q)))
# for i in range(len(q)):
#     for j in range(i, len(q), 1):
#         if(l[i] < l[j]):
#           t = l[j]
#           l[j] = l[i]
#           l[i] = t
#           t2 = z[j]
#           z[j] = z[i]
#           z[i] = t2
      
# write to file
# with open('sharc.txt', 'w') as f:
#     for line in z:
#         f.write("%d \n" % line)
        
#read from file
f = open("sharc.txt", "r")
lines = f.read().split("\n")
z = [eval(i) for i in lines]

f = open("sharc_test.txt", "r")
lines = f.read().split("\n")
z_test = [eval(i) for i in lines]


def select_samples(j, N, z, q, sn):
    yes = []
    no = []
    more_info = []
    dup = []
    i=j
    while(len(yes) < N):
        x = z[i]
        if q[x] == "Yes" and sn[x] not in dup:
            dup.append(sn[x])
            yes.append(x)
        i+=1
            
    i = j
    while(len(no) < N):
        x = z[i]
        if q[x] == "No" and sn[x] not in dup:
            dup.append(sn[x])
            no.append(x)
        i+=1    
    
    i = j
    while(len(more_info) < N):
        x = z[i]
        if q[x] != "Yes" and q[x] != "No" and sn[x] not in dup:
            dup.append(sn[x])
            more_info.append(x)
        i+=1        
    return yes + no + more_info

ind = select_samples(0, N, z, q, sn)
ind_test = select_samples(0, N, z_test, q_test, sn_test)
sn = [data[i]["snippet"] for i in ind]
q = [data[i]["question"] for i in ind]
sc = [data[i]["scenario"] for i in ind]
hist = [data[i]["history"] for i in ind]


os.environ["OPENAI_API_KEY"] = "YOUR OPEN AI KEY"
client = OpenAI()
# completion = client.chat.completions.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
#     {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
#   ]
# )


j = 149
messages =[]
messages.append({"role": "system", "content": "You are a friendly and helpful teaching assistant. You explain concepts in great depth using simple terms, and you give examples to help people learn. "})

for i in range(len(hist[j])):
  qs = "When asked, {0} I responded {1}".format(hist[j][i]['follow_up_question'], hist[j][i]['follow_up_answer'])
  # messages.append({"role": "system", "content": qs})
if sc[j] != "":
      messages.append({"role": "user", "content": sc[j]})

      
messages.append({"role": "user", "content": sn[j]})
messages.append({"role": "user", "content": "Yes or no or requires additional information or irrelevant"+ q[j]})
# messages.append({"role": "user", "content": "I am a federal benefit recipient"})

# messages.append({"role": "user", "content": sn[j]})
# messages.append({"role": "user", "content": "I did not bill privately with an account. Can my patient claim theire Medicare benefit electronically at my surgery?"})

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages = messages
)
print(completion.choices[0].message.content)


    

      