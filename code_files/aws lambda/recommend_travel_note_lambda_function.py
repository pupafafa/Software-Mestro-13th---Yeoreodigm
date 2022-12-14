import json
import pandas as pd
import psycopg2
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
import datetime

def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db

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
  

  
  survey_result = result[0]
  
  print(survey_result)

  theme_score = np.array([0]*22)
  theme_score = theme_score.reshape(1,-1)
  for place in survey_result:
    load_place_sql = f'SELECT theme FROM places_analysis WHERE place_id={place}'
    cursor.execute(load_place_sql)
    place_theme = cursor.fetchone()
    
    theme_score += np.array(place_theme)*2
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
      theme_score += np.array(place_theme)*5
  
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

#????????? ??????????????? ???????????? ?????? (????????? ??????)
def retrieve_taste(user_id,db):
  info = retrieve_taste_db(user_id,db)
  cursor =db.cursor()
  if info != None: 
    if (datetime.date.today() - info[1].date()).days>=3:
      updated_taste = calculate_taste(user_id,db)
      db_updated_taste = list(map(int, updated_taste[0]))
      print("db_updated_taste : ",db_updated_taste)
      #sql = "update user_taste set taste = %s where user_id = %s,"(db_updated_taste,user_id)
      #update db
      cursor.execute("update user_taste set taste = %s, last_update = %s where user_id = %s",(db_updated_taste,datetime.datetime.now() , user_id))
      db.commit()
    else:
      print("db?????? ????????? ???????????? ?????????!!")
      return np.array(info[0]).reshape(1,-1)
  else:
    print("calculate new")
    updated_taste = calculate_taste(user_id,db)
    db_updated_taste = list(map(int, updated_taste[0]))
    #insert new row to db
    cursor.execute("INSERT INTO user_taste(user_id,taste) VALUES(%s, %s)",(user_id,db_updated_taste))
    db.commit()
    
  return updated_taste

def load_course(day,db,location):
  if day>=25:
    day = 25
    location = []
  cursor= db.cursor()
  min_length = 2*day
  max_length = 4*day
  count = 0
  location_count = len(location)
  if location_count == 4 or location_count == 0:
    location_sql = ' and 1=1'
  #case 2 : ??? ????????? ????????? ?????? 
  elif location_count == 1:
    if day>=10:
      location_sql = ' and 1=1'
    else:
      location_sql = f" and LOWER(main_location) = \'{location[0]}\'"
  #case 3 : ?????? ????????? ????????? ??????
  else:
    if location_count == 2:
      location_sql = f" and main_location = 'Mixed' and {location[0]} >0 and {location[1]} >0"
    elif location_count == 3:
      location_sql = f" and main_location = 'Mixed' and {location[0]} >0 and {location[1]} >0 and {location[2]} >0"

  df = pd.DataFrame()

  #places??? 80???(???????????? ?????????)??? ???????????? ????????? ??????
  exclude_love_land_sql = " and 80 != ALL(places)"

  load_course_sql= (f"SELECT id, theme, score, places FROM course_ WHERE length>={min_length} and length<={max_length}" + location_sql + exclude_love_land_sql)
  #?????? query????????? query ????????? ????????? ????????? ???????????????.
  
  cursor.execute(load_course_sql)
  result = cursor.fetchall()

  df =pd.DataFrame(result)
  
  #?????? ????????? ???????????? ????????? ?????? ??????
  if df.empty:
    print("no course")
    return df

  df.columns = ['id','theme','score','places']

  return df
  #intersect ?????? place??? ?????? df??? Places list??? append ????????????.

  
def recommend_travel_note(user_id, num_of_result,db):
  day=3
  location = ['east','west','south','north'] #??????????????? ?????? (?????? ????????????)
  course = load_course(day,db,location)
  course_size = len(course)

  if course.empty:
    print("empty course")
    return None

  user_taste = retrieve_taste(user_id,db)
  course['user_rating'] = course['theme'].apply(lambda x: np.sum(x*user_taste))
  #?????? ????????? ?????? ?????? 10???????????? ????????????
  course = course.sort_values('user_rating',ascending = False)
  high_score_items_id = course.iloc[:course_size//10][['id','score']]
  print("high_score_items_id ?????? ?????? ?????? ??????: ",high_score_items_id)
  
  ##????????? ?????? ????????? ?????? ?????? 50???????????? ??? ????????????.
  high_score_items_id = high_score_items_id.sort_values(by='score',ascending= False)
  high_score_items_id = list(high_score_items_id.iloc[:len(high_score_items_id)//2]['id'].values)
  print("high_score_items_id ????????? ??? 50%: ",high_score_items_id)
  
  #????????? ?????? ?????? ???????????? ???????????????
  
  result = high_score_items_id[:num_of_result]
  result = list(map(int,result)) #to use json format,  convert int64 to int

  return result
  

def lambda_handler(event, context):

  id = int(event['queryStringParameters']['memberId'])
  num_of_result = int(event['queryStringParameters']['numOfResult'])

  try:
    db = load_db()
  except:
        return {
            "success": False,
            "message": "Database Error",
        }
  result = recommend_travel_note(id,num_of_result,db)
  if result == []:
    return {
      'statusCode': 200,
      'body': json.dumps({  
                            "courseList" : "[No corresponding course]",
                            })
  }
  
  

  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "noteList" : result,
                            })
  }
  