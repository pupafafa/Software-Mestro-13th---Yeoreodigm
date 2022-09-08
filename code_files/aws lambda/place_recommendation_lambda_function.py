
import json
import pandas as pd
import psycopg2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
import datetime

def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db

#db에서 가져오는 함수
def retrieve_taste_db(user_id,db):
  cursor = db.cursor()
  sql = f"SELECT taste,last_update from user_taste where user_id={user_id}"
  cursor.execute(sql)
  result = cursor.fetchone()
  return result
  
def calculate_taste(user_id,db):
  print("calculate_tast...")
  cursor = db.cursor()
  #1. retrieve from survey
  load_survey_sql = f'SELECT result FROM survey_result WHERE member_id = {user_id};'
  cursor.execute(load_survey_sql)
  result = cursor.fetchone()
  

  try:
    survey_result = result[0]
  except Exception as e:
    print("해당 유저가 존재하지 않습니다.")

  print(survey_result)

  theme_score = np.array([0]*22)
  theme_score = theme_score.reshape(1,-1)
  for place in survey_result:
    load_place_sql = f'SELECT theme FROM places_analysis WHERE place_id={place}'
    cursor.execute(load_place_sql)
    place_theme = cursor.fetchone()
    
    theme_score += np.array(place_theme)*10
  #2. retrieve from place-like log
  load_like_log_sql = f'SELECT place_id FROM place_like WHERE member_id = {user_id};'
  cursor.execute(load_like_log_sql)
  user_like_log = cursor.fetchall()
  if user_like_log:
    user_like_log = list(map(lambda x: x[0],user_like_log))
    for place in user_like_log:
      load_place_sql = f'SELECT theme FROM places_analysis WHERE place_id={place}'
      cursor.execute(load_place_sql)
      place_theme = cursor.fetchone()
      theme_score += np.array(place_theme)*7
  
  #3. retrieve from place_click log
  load_click_log_sql = f'SELECT place_id FROM places_log WHERE member_id = {user_id};'
  cursor.execute(load_click_log_sql)
  user_click_log = cursor.fetchall()
  if user_click_log:
    user_click_log = list(map(lambda x: x[0],user_click_log))
    for place in user_click_log:
      load_place_sql = f'SELECT theme FROM places_analysis WHERE place_id={place}'
      cursor.execute(load_place_sql)
      place_theme = cursor.fetchone()
      theme_score += np.array(place_theme)
  print("calculate_tast DONE!!")
  print("user's taste : ",theme_score.reshape(1,-1))
  return theme_score.reshape(1,-1)

def load_place(db):
  cursor = db.cursor()
  sql = "SELECT place_id,theme from places_analysis"
  cursor.execute(sql)
  result = cursor.fetchall()
  attraction = pd.DataFrame(result)
  attraction.columns = ['id','theme']
  return attraction

def retrieve_taste(user_id,db):
  info = retrieve_taste_db(user_id,db)
  cursor =db.cursor()
  if info != None: 
    if (datetime.date.today() - info[1].date()).days>=3:
      print("update calcuate")
      updated_taste = calculate_taste(user_id,db)
      db_updated_taste = list(map(int, updated_taste[0]))
      #update db
      sql = f"update user_taste set taste = ARRAY{db_updated_taste} where user_id = {user_id}"
      cursor.execute(sql)
      db.commit()
    else:
      print("db에서 그대로 가져와서 빨라용!!")
      return np.array(info[0]).reshape(1,-1)
  else:
    print("calculate new")
    updated_taste = calculate_taste(user_id,db)
    db_updated_taste = list(map(int, updated_taste[0]))
    #insert new row to db
    cursor.execute("INSERT INTO user_taste(user_id,taste) VALUES(%s, %s)",(user_id,db_updated_taste))
    db.commit()
    
  return updated_taste


def recommend_place(user_id,places_in_course,num_of_result):
  db= load_db()
  attraction = load_place(db)
  user_taste = retrieve_taste(user_id,db)
  attraction['user_rating'] = attraction['theme'].apply(lambda x: np.sum(x*user_taste))
  #취향 점수가 높은 상위 10퍼센트만 선택하기
  attraction = attraction.sort_values('user_rating',ascending = False)
  high_score_items_id = list(attraction.iloc[:100]['id'].values)
  #index가 낮은(인기도가 높은 여행지 상위 20퍼센트만 선택하기)
  high_score_items_id.sort()
  print("high score items  : ",high_score_items_id)
  top20 = high_score_items_id[:30]
  top100 = high_score_items_id[:100]
  result = random.sample(top20, num_of_result)
  #이미 course에 있는 여행지가 뽑힌 경우 다시 뽑기
  count = 0
  while set(places_in_course).intersection(set(result)) != set():
    #상위 30개 여행지랑 계속 곂칠 수 밖에 없는 경우..
    if count > 10:
      result = random.sample(top100, num_of_result)
    else:
      result = random.sample(top20, num_of_result)
    count += 1
  
  result = list(map(int,result)) #to use json format,  convert int64 to int
  return result


def lambda_handler(event, context):
  # TODO implement
  id = int(event['queryStringParameters']['memberId'])
  places_in_course = event['queryStringParameters']['placesInCourse'].split(',')
  num_of_result = int(event['queryStringParameters']['numOfResult'])

  try:
    db = load_db()
  except:
    return {
            'statusCode': 500,
            "success": False,
            "message": "Database Error",
            
            
        }
        
  place_list = recommend_place(id,places_in_course,num_of_result)
  
  

  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "placeList" : place_list,
                            })
  }
