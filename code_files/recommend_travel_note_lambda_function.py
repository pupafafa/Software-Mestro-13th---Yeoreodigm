import json
import pandas as pd
import psycopg2
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity

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
    #print('place : ',place,"\tnow : ",place_theme)

  result = theme_score / len(survey_result)
  return result

def load_course(day,db):
  cursor= db.cursor()
  min = day*3
  max = day*4
  load_course_sql= (f"SELECT id,title,nature,outdoor,fatigue,sea,walking,exciting,day,culture,cluster,places, main_location FROM course_ where length>={min} and length <={max}")
  #해당 query문으로 query 날려서 결과가 있는지 확인해야함.
      
  cursor.execute(load_course_sql)
  result = cursor.fetchall()

  df = pd.DataFrame(result)
  df.columns = ['id','title','nature','outdoor','fatigue','sea','walking','exciting','day','culture','cluster','places','main_location']

  return df
  #intersect 밖의 place를 모든 df의 Places list에 append 해줘야함.
  
def recommend_by_theme(user_id, num_of_result,db):
  top = num_of_result
  day = 3
  course = load_course(day,db)
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
      
  #print('similarity : ',similarity)
  
  result_index = similarity.argsort()
  result_index = result_index
  
  #print("result_index : ",result_index)

  for i in range(-1,-11,-1):
    now_idx = result_index[i]
    sim = similarity[now_idx]
    print("similarity : ",sim,"df index : ",now_idx)

  top_N_result = result_index[-1:-(top+1):-1]
  print("top_N_result",top_N_result)
  
  #결과는 가장 일치율이 높은거 1개의 index만 던져주자
  result = top_N_result[0:top]
  result_df = course.iloc[result]
  print(result_df)
  return list(map(int,result_df['id'].values)) #to use json format,  convert int64 to int
  

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
  result = recommend_by_theme(id,num_of_result,db)
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
  