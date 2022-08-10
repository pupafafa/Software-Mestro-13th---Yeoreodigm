import json
import pandas as pd
import psycopg2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import random
import os

def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db

def find_places_in_travel_note(travel_note_id, db):
  cursor= db.cursor()
  sql = f"select places from course where travel_note_id={travel_note_id}"
  cursor.execute(sql)
  result = cursor.fetchall()
  for places in result:
    print(places)
  places = []
  for path in result:
    places += path[0]
  return places
  
def calculate_taste(user_id,db):
  print("calculate_tast...")
  cursor = db.cursor()
  load_survey_sql = f'SELECT result FROM survey_result WHERE member_id = {user_id};'
  cursor.execute(load_survey_sql)
  result = cursor.fetchone()
  survey_result = result[0]
  print(survey_result)

  theme_score = np.array([0]*8)
  for place in survey_result:
    load_place_sql = f'SELECT nature,outdoor,fatigue,sea,walking,exciting,day,culture FROM places_analysis WHERE place_id={place}'
    cursor.execute(load_place_sql)
    place_theme = cursor.fetchone()
    
    theme_score += np.array(place_theme)
    #print('place : ',place,"\tnow : ",place_theme)

  avg_theme_score = theme_score / len(survey_result)
  user_taste = pd.DataFrame(avg_theme_score.reshape(1,-1))
  user_taste.columns = ['nature','outdoor','fatigue','sea','walking','exciting','day','culture']
  print("calculate_tast DONE!!")
  return user_taste

def load_place(db):
  cursor= db.cursor()
  
  load_place_sql= f'SELECT place_id,nature,outdoor,fatigue,sea,walking,exciting,day,culture,cluster FROM places_analysis'
  cursor.execute(load_place_sql)
  result = cursor.fetchall()
  df = pd.DataFrame(result)
  df.columns = ['place_id','nature','outdoor','fatigue','sea','walking','exciting','day','culture','cluster']
  df = df.sort_values(by='place_id',ascending=True)
  return df

import json
import pandas as pd
import psycopg2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import random
import os

def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db

def find_places_in_travel_note(travel_note_id, db):
  cursor= db.cursor()
  sql = f"select places from course where travel_note_id={travel_note_id}"
  cursor.execute(sql)
  result = cursor.fetchall()
  for places in result:
    print(places)
  places = []
  for path in result:
    places += path[0]
  return places
  
def calculate_taste(user_id,db):
  print("calculate_tast...")
  cursor = db.cursor()
  load_survey_sql = f'SELECT result FROM survey_result WHERE member_id = {user_id};'
  cursor.execute(load_survey_sql)
  result = cursor.fetchone()
  survey_result = result[0]
  print(survey_result)

  theme_score = np.array([0]*8)
  for place in survey_result:
    load_place_sql = f'SELECT nature,outdoor,fatigue,sea,walking,exciting,day,culture FROM places_analysis WHERE place_id={place}'
    cursor.execute(load_place_sql)
    place_theme = cursor.fetchone()
    
    theme_score += np.array(place_theme)
    #print('place : ',place,"\tnow : ",place_theme)

  avg_theme_score = theme_score / len(survey_result)
  user_taste = pd.DataFrame(avg_theme_score.reshape(1,-1))
  user_taste.columns = ['nature','outdoor','fatigue','sea','walking','exciting','day','culture']
  print("calculate_tast DONE!!")
  return user_taste

def load_place(db):
  cursor= db.cursor()
  
  load_place_sql= f'SELECT place_id,nature,outdoor,fatigue,sea,walking,exciting,day,culture,cluster FROM places_analysis'
  cursor.execute(load_place_sql)
  result = cursor.fetchall()
  df = pd.DataFrame(result)
  df.columns = ['place_id','nature','outdoor','fatigue','sea','walking','exciting','day','culture','cluster']
  df = df.sort_values(by='place_id',ascending=True)
  return df

def recommend_place(user_id,travel_note_id):
  
  top = 50
  db = load_db()
  place = load_place(db)
  user_taste = calculate_taste(user_id,db)
  places_in_course = find_places_in_travel_note(travel_note_id, db)
  tag = ['nature','outdoor','fatigue','sea','walking','exciting','day','culture']
  

  #entire tag
  print(user_taste)
  entire_similarity = cosine_similarity(user_taste, place[tag])
  entire_similarity = entire_similarity[0]
      
  print('entire similarity : ',entire_similarity)
  
  result_index = entire_similarity.argsort()
  
  print("result_index : ",result_index)


  for i in range(-1,-4,-1):
    now_idx = result_index[i]
    sim = entire_similarity[now_idx]
    print("now place ",place.iloc[now_idx])
    print("similarity : ",sim,"df index : ",now_idx)
    

  top_N_result = result_index[-1:-(101):-1]
  print("top_N_similart_result",top_N_result[:10])
  
  result = place.iloc[top_N_result].sort_values(by='place_id',ascending=True)
  result = result.iloc[:top]
  print("***************************************result***************************************")
  print(result)

  #
  result_copy = result.copy() #다시 뽑을 경우를 대비해서 원본 복사본 만들어놓기.
  result = random.sample(list(result['place_id']), 2) 
  # if course에 있는거랑 곂치면 다시 뽑자!!!
  while set(result).intersection(places_in_course) != set():
    result = random.sample(list(result_copy['place_id']), 2)

  places_in_course += result

  
  print("result **id** list",result)
  
  print("*"*50)

  #6개 태그만 적용하기
  #2개를 뽑아서 없앤다음, 적용하자.4개중 nature, exciting, culture, day
  six_tag = tag.copy()
  picking_list = ['nature', 'exciting', 'sea', 'day']
  randomly_chosen_two_tags = random.sample(picking_list,2)
  for tag in randomly_chosen_two_tags:
    six_tag.remove(tag) #뽑힌 2개는 지워주기

  user_taste_six = user_taste[six_tag]
  print("user taste six : ",user_taste_six)
  six_tag_similarity = cosine_similarity(user_taste_six, place[six_tag])
  six_tag_similarity = six_tag_similarity[0]
  
  print('six similarity : ',six_tag_similarity)
  
  six_result_index = six_tag_similarity.argsort()
  
  print("six result_index : ",six_result_index)

  for i in range(-1,-4,-1):
    now_idx = six_result_index[i]
    sim = six_tag_similarity[now_idx]
    print("now place ",place.iloc[now_idx])
    print("similarity : ",sim,"df index : ",now_idx)
    
  top_N_result_six = six_result_index[-1:-101:-1]
  print("top_N_result(only six tag)",top_N_result_six[:10])
  
  result_six = place.iloc[top_N_result_six].sort_values(by='place_id',ascending=True)
  result_six = result_six.iloc[:top]
  print("result _ six")
  print(result_six)
  result_six_copy = result_six.copy() #다시 뽑을 경우를 대비해서 원본 복사본 만들어놓기.
  result_six = random.sample(list(result_six['place_id']), 2) # if 위에서 뽑은거랑 곂치면 다시 뽑자!!!
  while set(result_six).intersection(places_in_course) != set():
    result_six = random.sample(list(result_six_copy['place_id']), 2)

  
  final_result = result+result_six

  return final_result


def lambda_handler(event, context):
  # TODO implement
  id = int(event['queryStringParameters']['memberId'])
  travel_note_id = int(event['queryStringParameters']['travelNoteId'])
  try:
    db = load_db()
  except:
    return {
            'statusCode': 500,
            "success": False,
            "message": "Database Error",
            
            
        }
        
  place_list = recommend_place(id,travel_note_id)
  
  

  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "placeList" : place_list,
                            })
  }


def lambda_handler(event, context):
  # TODO implement
  id = int(event['queryStringParameters']['memberId'])
  travel_note_id = int(event['queryStringParameters']['travelNoteId'])
  try:
    db = load_db()
  except:
    return {
            'statusCode': 500,
            "success": False,
            "message": "Database Error",
            
            
        }
        
  place_list = recommend_place(id,travel_note_id)
  
  

  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "placeList" : place_list,
                            })
  }