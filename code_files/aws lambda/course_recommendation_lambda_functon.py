import json
import pandas as pd
import psycopg2
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
from itertools import combinations

def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db

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
  
  cursor.execute(load_course_sql)
  result = cursor.fetchall()

  df =pd.DataFrame(result)
  
  #해당 조건에 만족하는 코스가 없는 경우
  if df.empty:
    print("no course")
    return df

  df.columns = ['id','theme','score','places']

  return df
  #intersect 밖의 place를 모든 df의 Places list에 append 해줘야함.




def recommend_by_theme(user_id, day, include_list,location,db):
  top = 10
  course = load_course(day,db,location)
  course_size = len(course)

  if course.empty:
    print("empty course")
    return None

  user_taste = calculate_taste(user_id,db)
  course['user_rating'] = course['theme'].apply(lambda x: np.sum(x*user_taste))
  #취향 점수가 높은 상위 10퍼센트만 선택하기
  course = course.sort_values('user_rating',ascending = False)
  high_score_items_id = course.iloc[:course_size//10][['id','score']]
  print("high_score_items_id 취향 점수 기반 탑텐: ",high_score_items_id)
  
  ##여기서 평균 인기도 기준 상위 50퍼센트만 또 뽑아내기.
  high_score_items_id = high_score_items_id.sort_values(by='score',ascending= False)
  high_score_items_id = list(high_score_items_id.iloc[:len(high_score_items_id)//2]['id'].values)
  print("high_score_items_id 인기도 탑 50%: ",high_score_items_id)
  
  #여기서 1등을 한 놈 반환해주자
  result_id = high_score_items_id[0]
  result_places = course.loc[course['id']==result_id,['places']].values[0][0]
  print("result_places : ",result_places)
  
  #이미 course에 있는 여행지가 뽑힌 경우 다시 뽑기
  
  not_included = list(set(include_list) - set(result_places) )
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
  result_path = recommend_by_theme(id, day,include,location,db)
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
  