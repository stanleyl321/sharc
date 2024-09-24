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

file = open("ConditionalQA/v1_0/dev.json")
data = json.load(file)

file = open("ConditionalQA/v1_0/documents.json")
docs = json.load(file)

file = open("ConditionalQA/CondQA_template.txt")
isrn = file.read()
# file = open("sharc1-official/json/sharc_test.json")
# test_data = json.load(file)

urls = [i["url"]for i in data]
q = [i["answers"] for i in data]
l = [len(i) for i in urls]
N = 33

dup = []

for i in range(len(urls)):
    url = urls[i]
    if url not in dup:
        dup.append(url)
# sn_test = [i["snippet"] for i in test_data]
# q_test = [i["answer"] for i in test_data]

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

# ind = select_samples(0, N, z, q, sn)
# ind_test = select_samples(0, N, z_test, q_test, sn_test)
def select_answerable(N, data):
    ind = []
    j = 0
    for i in range(len(data)):
        if data[i]["not_answerable"]:
            continue
        ind.append(i)
        j += 1
        if j >= N:
            return ind
        
ind = select_answerable(N, data)
url = [data[i]["url"] for i in ind]
q = [data[i]["question"] for i in ind]
sc = [data[i]["scenario"] for i in ind]
an = [data[i]["answers"] for i in ind]
# hist = [data[i]["history"] for i in ind]


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
            csvw.writerow([url[j], sc[j], q[j], conditional_answer(j), answers[j]])
        csvw.writerow(["{}/{}".format(total, len(ind))])

def shot(j, ans):
    messagef = "Snippet: {} \n Scenario: {} \n Q: {} \n Based on the information in the snippet and scenario, \n {}"
    return messagef.format(url_get_snippet(url[j]), sc[j], q[j], ans)

def url_get_snippet(url):
    for doc in docs:
        if doc['url'] == url:
            return doc['contents'] 
    return ""

def conditional_answer(j):
    answer = ""
    for i in range(len(an[j])):
        a = an[j][i]
        answer = f'{answer} A{i+1}: {a[0]} \n'
        if len(a[1]) > 0:
            answer = f'{answer} Conditions: \n'
        for k in range(len(a[1])):
            answer = f'{answer} {a[1][k]} \n'
    return answer


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

def format_longshort(long, short):
    return f'Long answer: {long} \n Short answer: {short}'
def format_message(shoty, shotn, shotm):
    isrn = "In the following text, you will be given three examples of questions and answers and you will provide a fourth answer given a one more question. You will provide a long answer and a short answer with conditions. "
    return isrn
long_answerm = """Tax Liability on Foster Care Allowance
Tax Exemption:

You can receive up to £10,000 per household tax-free from fostering each year. This amount is not subject to income tax.
Tax Relief:

In addition to the £10,000 tax exemption, you can claim tax relief for each week (or part week) that a child is in your care. The relief rates are:
Under 11 years old: £200 per child per week
11 years old or over: £250 per child per week"""
long_answery = """As a special guardian, you have substantial day-to-day responsibility for your nephew, but there are certain limitations and requirements to be aware of if you plan to take him to live abroad.

Taking Your Nephew Abroad as a Special Guardian
Consent for Long-Term Travel:

As a special guardian, you need to obtain consent for specific significant decisions, including taking the child abroad for more than 3 months.
Since you plan to move to Boston for a year, this would exceed the 3-month threshold.
Obtaining Consent:

You will need to get the consent of everyone who has parental responsibility for your nephew. This might include his birth parents or other legal guardians if applicable.
If you cannot get this consent, you will need to apply to the court for permission. You would use the form "Make an application in existing court proceedings related to children" (form C2) to request this.
Court Application:

To ensure everything is legally in order, you should seek a court order to take your nephew abroad. This process involves submitting forms to your local family court and potentially attending hearings to explain your plans and why it is in the best interest of your nephew.
Local Authority Involvement:

If your nephew is under a care order or involved with children’s services, you might also need to inform the local council and get their agreement."""
long_answern = """Eligibility for Housing Benefit
Age Requirement:

You must be over State Pension age or living in supported, sheltered, or temporary housing to be eligible to claim Housing Benefit. Since you are 24, you do not meet the age requirement.
Housing Benefit Replacement:

Housing Benefit is being replaced by Universal Credit. If you are under State Pension age and do not fit into one of the specific categories that allow new claims for Housing Benefit (like supported, sheltered, or temporary housing), you generally need to claim Universal Credit instead.
Ineligible Situations:

If you are already claiming Universal Credit, you cannot claim Housing Benefit unless you are in temporary or supported housing.
As you are renting privately and do not fall into the supported, sheltered, or temporary housing categories, you would not be eligible to claim Housing Benefit.""
Consent for Long-Term Travel:

As a special guardian, you need to obtain consent for specific significant decisions, including taking the child abroad for more than 3 months.
Since you plan to move to Boston for a year, this would exceed the 3-month threshold.
Obtaining Consent:

You will need to get the consent of everyone who has parental responsibility for your nephew. This might include his birth parents or other legal guardians if applicable.
If you cannot get this consent, you will need to apply to the court for permission. You would use the form “Make an application in existing court proceedings related to children” (form C2) to request this.
Court Application:

To ensure everything is legally in order, you should seek a court order to take your nephew abroad. This process involves submitting forms to your local family court and potentially attending hearings to explain your plans and why it is in the best interest of your nephew.
Local Authority Involvement:

If your nephew is under a care order or involved with children’s services, you might also need to inform the local council and get their agreement."""
shotm = shot(11, format_longshort(long_answerm, conditional_answer(11)))
shoty = shot(14, format_longshort(long_answery, conditional_answer(14)))
shotn = shot(18, format_longshort(long_answern, conditional_answer(18)))
print(ind[18], ind[14], ind[11])

ind.pop(18)
ind.pop(14)
ind.pop(11)

for j in range(len(ind)): 
    # h = ""
    # for i in range(len(hist[j])):
    #       qs = "When asked, {0} I responded {1}.".format(hist[j][i]['follow_up_question'], hist[j][i]['follow_up_answer'])
    #       h= f'{h} {qs}'
    # answer = conditional_answer(j)
    us = shot(j, "")
    shotpr2 = """ 
    
        """
    # message = f'{shoty} \n {shotn} \n {shotm} \n {us}'
    message = isrn.format(shoty, shotn, shotm, us)
    print(j)
    # message = f'{shotpr2} {us}'
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

    

      