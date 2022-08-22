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
    print('place : ',place,"\tnow : ",place_theme)

  result = theme_score / len(survey_result)
  return result


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

def load_course(day,db,include,location):
  if day>=25:
    day = 25
    location = []
  cursor= db.cursor()
  min_length = 2*day
  max_length = 4*day
  length = len(include)
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
  while length >= count:
    possible_cases = list(combinations(include,length-count))
    ##sql query 날리고 결과 받아서
    for now in possible_cases:
      print("now : ",list(now))
      now_include = list(now)
      load_course_sql= (f"SELECT id,title,nature,outdoor,fatigue,sea,walking,exciting,day,culture,cluster,places, main_location\
 FROM course_ WHERE length>={min_length} and length<={max_length} and array{now_include}::smallint[] <@ places" + location_sql + exclude_love_land_sql)
      #해당 query문으로 query 날려서 결과가 있는지 확인해야함.
      
      cursor.execute(load_course_sql)
      result = cursor.fetchall()

      #현재 포함시킬 place를 모두 가지는 코스가 없는경우 
      if len(result) == 0:
        continue
      #현재 Place를 모두 포함하는 코스가 있는경우
      else:
        print("현재 now를 포함하는 df : \n",pd.DataFrame(result),"\n****************************\n")
        df = pd.concat([df, pd.DataFrame(result)])
    
    #dataframe에 값이 존재하면 (최적의 코스를 찾았다면)
    if not df.empty:
      break    
    count += 1
  
  #해당 조건에 만족하는 코스가 없는 경우
  if df.empty:
    print("no course")
    return df

  df.columns = ['id','title','nature','outdoor','fatigue','sea','walking','exciting','day','culture','cluster','places','main_location']

  return df
  #intersect 밖의 place를 모든 df의 Places list에 append 해줘야함.



def recommend_by_theme(user_id, day, include_list,location,db):
  top = 10
  course = load_course(day,db,include_list,location)
  if course.empty:
    print("empty course")
    return None

  user_taste = calculate_taste(user_id,db)
  user_taste = user_taste.reshape(1,-1)

  tag = ['nature','outdoor','fatigue','sea','walking','exciting','day','culture']

  print(user_taste)
  
  similarity = cosine_similarity(user_taste, course[tag])
  similarity = similarity[0]
  print(similarity.shape)
      
  print('similarity : ',similarity)
  
  result_index = similarity.argsort()
  result_index = result_index
  
  print("result_index : ",result_index)

  for i in range(-1,-(len(result_index)+1),-1):
    now_idx = result_index[i]
    sim = similarity[now_idx]
    print("similarity : ",sim,"df index : ",now_idx)

  top_N_result = result_index[-1:-(top+1):-1]
  print("top_N_result",top_N_result)
  
  #결과는 가장 일치율이 높은거 1개의 index만 던져주자
  result = top_N_result[0]
  result_df = course.iloc[result]
   
  print(result_df)
  #꼭 넣어야할 애들이 아직 안들어 간게 있으면 따로 넣어주기
  not_included_places = list(set(include_list) - set(result_df['places']))
  if 0 not in include_list:
    result_df['places'] += not_included_places
  
  path = path_divider(day,result_df['places'])
  print('path : ',path)
  return path
    
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
  