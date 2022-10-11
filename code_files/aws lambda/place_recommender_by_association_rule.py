import json
import pandas as pd
import psycopg2
import os

def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db


def load_association_rule(db):
  sql = "select * from association_rule"
  cursor = db.cursor()
  cursor.execute(sql)
  result = cursor.fetchall()
  rule = pd.DataFrame(result)
  rule.columns = ['id','antecedents','consequents']
  return rule

def recommend_by_assoc_rule(input,association_rule):
  recommend_list = []
  for antecedents,consequents in zip(association_rule['antecedents'].values,association_rule['consequents'].values):
    match_rate = len(set(input).intersection(set(antecedents))) / len(antecedents)
    if match_rate >=1.0 : #cause를 가진다면
      #print(consequents)
      recommend_list += consequents
      
  #print(set(recommend_list))
  recommend_list = list(set(recommend_list) - set(input))
  
  return recommend_list


def lambda_handler(event, context):
    
    places_in_course = list(map(int,event['queryStringParameters']['placesInCourse'].split(',')))
    db = load_db()
    rule = load_association_rule(db)
    result = recommend_by_assoc_rule(places_in_course,rule)
    

    return {
        'statusCode': 200,
        'body': json.dumps({  
                              "placeList" : result,
                              })
    }
