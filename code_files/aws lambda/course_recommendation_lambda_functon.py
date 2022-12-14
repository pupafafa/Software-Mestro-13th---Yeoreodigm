import json
import pandas as pd
import psycopg2
import numpy as np
import os
import random
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

def load_course(day,db,location):
  if day>=12:
    day = 11
    location = []
  cursor= db.cursor()
  min_length = 2*day
  max_length = 4*day
  count = 0
  location_count = len(location)
  if location_count == 4 or location_count == 0:
    location_sql = ' and 1=1'
  #case 2 : 한 지역만 선택한 경우 
  elif location_count == 1:
    if day>=10:
      location_sql = ' and 1=1'
    else:
      location_sql = f" and LOWER(main_location) = \'{location[0]}\'"
  #case 3 : 여러 지역을 선택한 경우
  else:
    if location_count == 2:
      location_sql = f" and main_location = 'Mixed' and {location[0]} >0 and {location[1]} >0"
    elif location_count == 3:
      location_sql = f" and main_location = 'Mixed' and {location[0]} >0 and {location[1]} >0 and {location[2]} >0"

  df = pd.DataFrame()

  #places가 80번(러브랜드 휴업중)을 포함하는 코스는 제외
  exclude_love_land_sql = " and 80 != ALL(places)"

  load_course_sql= (f"SELECT id, theme, score, places FROM course_ WHERE length>={min_length} and length<={max_length}" + location_sql + exclude_love_land_sql)
  #해당 query문으로 query 날려서 결과가 있는지 확인해야함.
  print("load_course_sql : " ,load_course_sql)
  cursor.execute(load_course_sql)
  result = cursor.fetchall()

  df =pd.DataFrame(result)
  
  #해당 조건에 만족하는 코스가 없는 경우
  if df.empty:
    print("no course")
    return df

  df.columns = ['id','theme','score','places']

  return df
  
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

def retrieve_taste(user_id,db):
  info = retrieve_taste_db(user_id,db)
  cursor =db.cursor()
  if info != None: 
    if (datetime.date.today() - info[1].date()).days>=3:
      print("update calcuate")
      updated_taste = calculate_taste(user_id,db)
      print("updated_taste: ",updated_taste)
      db_updated_taste = list(map(int, updated_taste[0]))
      print("db_updated_taste : ",db_updated_taste)
      #sql = "update user_taste set taste = %s where user_id = %s,"(db_updated_taste,user_id)
      #update db
      cursor.execute("update user_taste set taste = %s, last_update = %s where user_id = %s",(db_updated_taste,datetime.datetime.now() , user_id))
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


def path_divider(day,path):
  path_per_day = []
  checker = day

  length = len(path)
  print('length :',length )

  remainder = length%day
  quotient = length//day

  start = 0
  check=0

  while start<length:
    print(path[start:start + quotient + check])
    now_day_path = path[start:start + quotient + check]
    now_day_path = list(map(int,now_day_path))
    path_per_day.append(now_day_path)
    start += quotient+check
    checker-=1
    if checker<=remainder:
      check = 1

  return path_per_day


def recommend_course(user_id, day, include_list,location,db):
  top = 10
  course = load_course(day,db,location)
  course_size = len(course)

  if course.empty:
    print("empty course")
    return None

  user_taste = retrieve_taste(user_id,db)
  course['user_rating'] = course['theme'].apply(lambda x: np.sum(x*user_taste))
  #취향 점수가 높은 상위 10퍼센트만 선택하기
  print("course : \n",course)
  course = course.sort_values('user_rating',ascending = False)
  result_places = []
  if len(course) == 1:
    result_places = course['places'].values[0]
    print("result_places", result_places)
    result_places = list(map(int,result_places))
    return (path_divider(day,result_places))
  elif len(course) < 5:
    high_score_items_id = course[['id','score','user_rating']]
  elif len(course) < 10:
    high_score_items_id = course.iloc[:course_size//2][['id','score','user_rating']]
  elif len(course) < 20:
    high_score_items_id = course.iloc[:course_size//5][['id','score','user_rating']]
  else:
    high_score_items_id = course.iloc[:course_size//10][['id','score','user_rating']]
  
  

  print("high_score_items_id 취향 점수 기반 탑텐: ",high_score_items_id)
  
  ##여기서 평균 인기도 기준 상위 50퍼센트만 또 뽑아내기.
  high_score_items_id = high_score_items_id.sort_values(by='score',ascending= False)
  high_score_items_id = list(high_score_items_id.iloc[:len(high_score_items_id)//2]['id'].values)
  print("high_score_items_id 인기도 탑 30%: ",high_score_items_id)
  
  #여기서 랜덤으로 한 놈 반환해주자
  result_id = random.choice(high_score_items_id)
  result_places = course.loc[course['id']==result_id,['places']].values[0][0]
  print("result_places : ",result_places)
  
  #이미 course에 있는 여행지가 뽑힌 경우 다시 뽑기
  print("include_list : ",include_list)
  if 0 not in include_list:
    not_included = list(set(include_list) - set(result_places))
    result_places += not_included
  
  
  result_places = list(map(int,result_places)) #to use json format,  convert int64 to int

  result = path_divider(day,result_places)
  return result
    
def to_lower_case(string):
  return string.lower()
    
def lambda_handler(event, context):

  id = int(event['queryStringParameters']['id'])
  day = int(event['queryStringParameters']['day'])
  include = list(map(int,event['queryStringParameters']['include'].split(',')))
  location = event['queryStringParameters']['location'].split(',')
  location = list(map(to_lower_case, location) )
  try:
    db = load_db()
  except:
        return {
            "success": False,
            "message": "Database Error",
        }
  result_path = recommend_course(id, day,include,location,db)
  if result_path == None:
    return {
      'statusCode': 200,
      'body': json.dumps({  
                            "courseList" : "[No corresponding course]",
                            })
  }
  
  

  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "courseList" : result_path,
                            })
  }
  