from openai import OpenAI
import gradio 
import os
import re
from arango import ArangoClient
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('SECRET_KEY') or os.environ('SECRET_KEY')
DB_HOST = os.getenv('ARANGO_HOST') or os.environ('ARANGO_HOST')
DB_PASSWORD = os.getenv('ARANGO_PWD') or os.environ('ARANGO_PWD')
DB_PORT = os.getenv('ARANGO_PORT') or os.environ('ARANGO_PORT')
DB_NAME = os.getenv('ARANGO_DB_NAME') or os.environ('ARANGO_DB_NAME')

# Init the OpenAPI client
client = OpenAI(
  api_key=API_KEY
)

print(API_KEY)

# Initialize the ArangoDB client.
ArangoClient = ArangoClient(f"http://{DB_HOST}:{DB_PORT}")
db = ArangoClient.db(DB_NAME, username='root', password=DB_PASSWORD)

examples = """
# What are the symptoms of the disease Asthma?
WITH Symptom
FOR disease IN Disease
    FILTER disease.label == 'Asthma'
    FOR v, e, s IN 1..1 OUTBOUND disease hasSymptom
        RETURN v.label
# What are the symptoms of the disease Diabetes?
WITH Symptom
FOR disease IN Disease
    FILTER disease.label == 'Diabetes'
    FOR v, e, s IN 1..1 OUTBOUND disease hasSymptom
        RETURN v.label
# How to treat Asthma or what medications to use when suffering from Asthma or what are the treatments for Asthma?
WITH Treatment
FOR disease IN Disease
    FILTER disease.label == 'Asthma'
    FOR v, e, s IN 1..1 OUTBOUND disease isTreatedBy
        RETURN v.label
# How to treat COVID-19 or what medications to use when suffering from COVID-19 or what are the treatments for COVID-19?
WITH Treatment
FOR disease IN Disease
    FILTER disease.label == 'COVID-19'
    FOR v, e, s IN 1..1 OUTBOUND disease isTreatedBy
        RETURN v.label
# What kind of doctor do I look for if I am diagnosed with Asthma or What is the medical specialty for Asthma?
WITH MedicalSpecialty
FOR disease IN Disease
    FILTER disease.label == 'Asthma'
    FOR v, e, s IN 1..1 OUTBOUND disease hasSpecialty
        RETURN v.label
# What kind of doctor do I look for if I am suffering from Macular degeneration or What is the medical specialty for Macular degeneration?
WITH MedicalSpecialty
FOR disease IN Disease
    FILTER disease.label == 'Macular degeneration'
    FOR v, e, s IN 1..1 OUTBOUND disease hasSpecialty
        RETURN v.label
# I have symptoms of frequent urination and increase in thirst what type of disease it could be?
WITH Symptom, Disease
FOR symptom IN Symptom
    FILTER symptom.label IN ['Frequent urination', 'Increased thirst']
    FOR v, e, p IN 1..1 INBOUND symptom hasSymptom
        COLLECT disease = v.label INTO symptoms = symptom.label
        FILTER LENGTH(symptoms) == 2
        RETURN disease
# I have symptoms of loud snoring and excessive daytime sleepiness what type of disease it could be?
WITH Symptom, Disease
FOR symptom IN Symptom
    FILTER symptom.label IN ['Loud snoring', 'Excessive daytime sleepiness']
    FOR v, e, p IN 1..1 INBOUND symptom hasSymptom
        COLLECT disease = v.label INTO symptoms = symptom.label
        FILTER LENGTH(symptoms) == 2
        RETURN disease
# I have symptoms of chest pain and shortness of breath what type of disease it could be?
WITH Symptom, Disease
FOR symptom IN Symptom
    FILTER symptom.label IN ['Chest pain', 'Shortness of breath']
    FOR v, e, p IN 1..1 INBOUND symptom hasSymptom
        COLLECT disease = v.label INTO symptoms = symptom.label
        FILTER LENGTH(symptoms) == 2
        RETURN disease
# I have symptoms of whiteheads and blackheads, papules and pustules what type of disease it could be?
WITH Symptom, Disease
FOR symptom IN Symptom
    FILTER symptom.label IN ['Whiteheads and blackheads', 'Papules and pustules']
    FOR v, e, p IN 1..1 INBOUND symptom hasSymptom
        COLLECT disease = v.label INTO symptoms = symptom.label
        FILTER LENGTH(symptoms) >= 1
        RETURN disease
# I have symptoms of whiteheads and blackheads, papules and pustules what type of disease it could be?
WITH Symptom, Disease
FOR symptom IN Symptom
    FILTER symptom.label IN ['Whiteheads and blackheads', 'Papules and pustules']
    FOR v, e, p IN 1..1 INBOUND symptom hasSymptom
        COLLECT disease = v.label INTO symptoms = symptom.label
        FILTER LENGTH(symptoms) >= 1
        RETURN disease
# To find the disease associated with either one of the symptoms chest pain or shortness of breath.
WITH Symptom, Disease
FOR symptom IN Symptom
    FILTER symptom.label IN ['Chest pain', 'Shortness of breath']
    FOR v, e, p IN 1..1 INBOUND symptom hasSymptom
        COLLECT disease = v.label INTO symptoms = symptom.label
        FILTER LENGTH(symptoms) >= 1
        RETURN disease
# To find the disease associated with symptom of eye pain.
WITH Symptom, Disease
FOR symptom IN Symptom
    FILTER symptom.label IN ['Eye pain']
    FOR v, e, p IN 1..1 INBOUND symptom hasSymptom
        COLLECT disease = v.label INTO symptoms = symptom.label
        FILTER LENGTH(symptoms) >= 1
        RETURN disease

"""

content_hcb = f""" You are an AI system specializes in generating ArangoDB AQL queries based on example AQL queries.
Example ArangoDB AQL queries are: \n {examples} \n
You will refrain from providing explanations or additional information and solely focus on generating the ArangoDB AQL queries.
You will strictly adhere to generating ArangoDB AQL queries based on the given examples.
Do not provide any AQL queries that can't be deduced from AQL query examples. 
However, if the context of the conversation is insufficient, you will inform the user and specify the missing context.
I repeat, if the context of the conversation is insufficient please inform the user and specify the missing context.
"""
content_hlr = f""" You are an AI assistant specialized in generating text responses based on the provided information. 
Your role is to generate human-readable responses using the available information from the latest prompt. 
While providing answers, you will maintain the perspective of an AI assistant. 
It is important to note that you will not add any extra information that is not explicitly provided in the given prompt. 
You will strictly adhere to generating responses solely based on the available information. 
Once again, You will refrain from including any additional details that are not explicitly given in the prompt.
"""

def human_like_response(user_input):
    messages = [
        {"role": "system", "content": content_hlr}
    ]
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(model='gpt-4o-mini', messages=messages, temperature=0.5)
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply

# check for valid AQL query
def is_aql_query(query):
    try:
        db.aql.execute(query)
        return True 
    except Exception:
        return False
    
def HealthCareChatbot(user_input):    
    messages = [{"role": "system", "content": content_hcb}]
    messages.append({"role": "user", "content": user_input})
    completion = client.chat.completions.create(model='gpt-4o-mini', messages=messages, temperature=0.5)
    reply = completion.choices[0].message.content    
    messages.append({"role": "assistant", "content": reply})
    regex = r"^```aql([\s\w\S]+)```"
    
    if "`" in reply:
        m = re.search(regex, reply)
        reply = m.group(1)
    
    if is_aql_query(reply):
        docs = db.aql.execute(reply)
        response = [doc for doc in docs]
        if len(response) == 0:
              message = f"Apologise to the user as you don't have an information related to this particular disease, treatments, symptoms, or medical specialty. "
              response = human_like_response(message)
        else:
            response = human_like_response(",".join(response))
    else:
        message = f"Greet the user and ask more information related to diseases, treatments, symptoms, or medical specialty."
        response = human_like_response(message)
    return response

inputs = gradio.Textbox(lines=7, label="Chat with ArangoGPT")
outputs = gradio.Textbox(label="ArangoGPT Reply")
demo = gradio.Interface(fn=HealthCareChatbot, inputs=inputs, outputs=outputs, title="HealthCare Chatbot Backed by ArangoDB")

demo.launch(debug=True, share=False, server_name='0.0.0.0')
