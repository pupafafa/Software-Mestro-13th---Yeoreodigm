import json
import psycopg2
from sklearn.cluster import KMeans
import os 
def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  print(endpoint,dbname,user,password)
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db

def load_places_location(db, place_list):
  cursor = db.cursor()
  place_list = str(tuple(place_list))
  sql = f"select place_id, latitude, longitude from places where place_id in {place_list}"
  cursor.execute(sql)
  result = cursor.fetchall()
  result = list(map(list,result))
  return result
  
def optimize_course(place_info,day):
  save_id = []  
  result = [[] for _ in range(day)]
  for i in place_info:
    save_id.append(i[0])
  #id는 클러스터링에 무관하게 만들기
  for i in place_info:
    i[0] = 0
    
  kmeans = KMeans(n_clusters=day,random_state=0)
  kmeans = kmeans.fit(place_info)

  for idx, label in enumerate(kmeans.labels_):
    now = save_id[idx]
    result[label].append(now)
  
  return result
  
def lambda_handler(event, context):

  day = int(event['queryStringParameters']['day'])
  place_list = list(map(int,event['queryStringParameters']['placeList'].split(',')))
  

  try:
    db = load_db()
  except:
        return {
            "success": False,
            "message": "Database Error",
        }
  place_info = load_places_location(db, place_list)
  result = optimize_course(place_info,day)
  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "result" : result,
                            })
  }