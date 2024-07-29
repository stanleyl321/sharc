#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 13:53:38 2024

@author: stanleyliu
"""
import json
import numpy
import re
import csv
import os
import anthropic
from openai import OpenAI

file = open("sharc1-official/json/sharc_train.json")
data = json.load(file)

file = open("sharc1-official/json/sharc_test.json")
test_data = json.load(file)

sn = [i["snippet"]for i in data]
q = [i["answer"] for i in data]
l = [len(i) for i in sn]
N = 35

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

# Selects sample snippet indices given the answers and snippets which are unique
# N The number of each category
# z The list of indices of all samples in decreasing length order
# q The list of answers
# sn The list of snippets
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



def llm_util(prompt, s):
    if(s == 1):
        os.environ["OPENAI_API_KEY"] = "OPENAI_API_KEY"
        client = OpenAI()
        completion = client.chat.completions.create(
          model="gpt-3.5-turbo",
          messages = [
              {"role": "user", "content" : prompt}
              ]
        )
        return completion.choices[0].message.content
    elif (s== 2):
        model='claude-3-5-sonnet-20240620'
        os.environ["ANTHROPIC_API_KEY"] = "ANTHROPIC_API_KEY"
        client = anthropic.Anthropic()
        try:
          message = client.messages.create(
            max_tokens=4096,
            model=model,
            #temperature=0,  #changed from default of 1.0 on 6/27
            messages=[{"role": "user", "content": prompt}])
          return message.content[0].text
        except anthropic.BadRequestError as ex:
            return repr(ex)
      
        
def interpret_answer(s):
    S = s.lower()
    if re.search(r"\b^yes\b", S):
        return 0
    elif re.search(r"\b^no\b", S):
        return 1
    else:
        return 2
def interpret_answer2(s):
    completion = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages = [
          {"role": "user", "content" : "Is the following a yes, no, or undecisive answer {}".format(s)}
          ]
    )
    S = completion.choices[0].message.content.lower()
    if re.search(r"\b^yes\b", S):
        return 0
    elif re.search(r"\b^no\b", S):
        return 1
    else:
        return 2
    
def write_csv(file):
    with open(file, 'w', newline='') as csvfile:
        csvw = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for j in range(len(ind)):
            csvw.writerow([sn[j], sc[j], q[j], data[ind[j]]["answer"], answers[j], tdict[mark[j]]])
        csvw.writerow(["{}/{}".format(total, len(ind))])

def shot(j, ans):
    messagef = "Snippet: {} \n Scenario: {} \n Conversational history: {} \n Options: -yes, -no, -requires additional information \n Q: {} \n A: {}"
    h = ""
    for i in range(len(hist[j])):
          qs = "When asked, {0} I responded {1}.".format(hist[j][i]['follow_up_question'], hist[j][i]['follow_up_answer'])
          h= f'{h} {qs}'
    return messagef.format(sn[j], sc[j], h, q[j], ans)

tdict = {0 : "Yes", 1 : "No", 2 : "Requires additional information"}
mark = []
answers = []
# if i say "tell me in one or two sentences" I get a lot more decisive answers
# message1 = "{} \n {} \n {} \n Based on the information given, answer with yes or no or requires additional information. {}}"


# # zero-shot
# for j in range(len(ind)): 
#     h = ""
#     for i in range(len(hist[j])):
#           qs = "When asked, {0} I responded {1}.".format(hist[j][i]['follow_up_question'], hist[j][i]['follow_up_answer'])
#           h= f'{h} {qs}'
    
#     message = message1.format(sn[j], h, sc[j], q[j]) 
    
#     completion = client.chat.completions.create(
#       model="gpt-3.5-turbo",
#       messages = [
#           {"role": "user", "content" : message}
#           ]
#     )
#     answers.append(completion.choices[0].message.content)
#     mark.append(interpret_answer(answers[j]))

# 3-shot
# shoty = shot(0, "Yes")
# shotn = shot(11, "No")
# shotm = shot(22, "Requires additional information")
# print(ind[22], ind[11], ind[0])

ind.pop(70)
ind.pop(35)
ind.pop(0)

for j in range(len(ind)): 
    h = ""
    for i in range(len(hist[j])):
          qs = "When asked, {0} I responded {1}.".format(hist[j][i]['follow_up_question'], hist[j][i]['follow_up_answer'])
          h= f'{h} {qs}'
    us = shot(j, "")
    
    shotpr2 = """ Snippet: The Direct Express® card is a prepaid debit card option for federal benefit recipients to receive their benefits electronically.  With the Direct Express® card, your federal benefit payment is automatically deposited directly into your card account each month on your payment day. This prepaid debit card offers the convenience and security of to spend and access your money rather than using cash for purchases.  Cardholders can make purchases at stores that accept Debit MasterCard®, pay bills, purchase money orders from the U.S. Post Office and get cash from ATMs or financial institutions that display the MasterCard® acceptance mark. No bank account or credit check is required to enroll. There are no sign-up fees or monthly account fees. Many card services are free. Additional information about the Direct Express® card is available at www.USDirectExpress.com. 
      Scenario:  None
      Converstional History: When asked, Are you a federal benefit recipient? I responded Yes. 
      Options:-yes,-no,-requires additional information 
      Q: Should I apply for this card? 
      A: Yes, I should apply for this card. Since I am a federal benefit recipient I am able to receive my benefits electronically. Additionally this card offers the convenience and security of to spend and access your money rather than using cash for purchases, and there are no sign-up fees, monthly account fees and many card services are free. 

      Snippet: ## Designated Provider

    To be a designated provider for a qualifying medical marijuana patient, the person must be:

    * Twenty-one years of age or older;
    * Named on the patient's medical marijuana authorization form.
    * Have a fully completed form also printed on tamper-resistant paper. The patient signs his or her copy of the authorization form, and the designated provider signs his or her own copy; and
    * Entered into the medical marijuana database and have a designated provider recognition card, if the patient chooses to be entered into the database. 
      Scenario: I already filled out all the paperwork.  I made sure I signed everything that needed to be signed. 
      Conversational History: When asked, Are you age 21 or older? I responded Yes. When asked, Are you named on the patient's medical marijuana form? I responded Yes. When asked, Have you fully completed and printed required forms? I responded Yes. When asked, Has the patient signed his or her copy of the authorization form? I responded Yes. When asked, Has the designated provider signed his or her own copy? I responded No. 
      Options:-yes,-no,-requires additional information 
      Q: Can I be a designated provider for this person? 
      A: No, I can't be a designated provider for this person. The designated provider has not provided his or her own copy. 

      Snippet: In order to be eligible for this program:

    * You must be a U.S. citizen,
    * You must have a good credit and earnings record, net worth, and liquidity behind the project,
    * Your project must be fully secured with your assets, including personal guarantees (non-recourse credit is not available), and
    * You should have at least a three year history of owning or operating the fisheries project which will be the subject of your proposed application, or a three year history owning or operating a comparable project. 
      Scenario: The project is fully secured with my assets. 
      Conversational History: When asked, Are you a US citizen? I responded Yes. When asked, Do you have at least 3 years history owning or operating  a fishery or comparable project? I responded Yes. 
      Options:-yes,-no,-requires additional information
      Q: Am I eligible for this program? 
      A: Requires additional information. You must have good credit and earnings record behind the project for you to be eligible for the program. Since you have not confirmed that you have good credit and earnings record, it is uncertain if you are eligible for the program.
        """
    # message = f'{shoty} \n {shotn} \n {shotm} \n {us}'
    print(j)
    message = f'{shotpr2} {us}'
    answer = llm_util(message, 2)
    answers.append(answer)
    mark.append(interpret_answer(answers[j]))
    
    
total = 0
for i in range(len(ind)):
    if i//N == mark[i]:
        total+=1;

write_csv('sharc_sample_results.csv')

#TODO: copy all stuff into into condqa shots with 3 shots, using dev and train set    

# print(completion.choices[0].message.content)
# for i in range(len(ind)):
#     print(answers[i] + "\n")
# print("Correct: {}/{}".format(total, len(ind)))

    

      