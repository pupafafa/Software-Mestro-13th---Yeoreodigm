import json
import psycopg2
from sklearn.cluster import KMeans
import os 
import math
import numpy as np


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
  
def calculate_distance(A,B):
  A_x = A[1]
  A_y = A[2]
  B_x = B[1]
  B_y = B[2]
  dist = math.sqrt((A_x - B_x)**2 + (A_y - B_y)**2)
  return dist
  
def make_dist_matrix(location_list):
  matrix_size = len(location_list)
  #initialize empty n*n matrix
  dist_matrix = [([0] * matrix_size) for _ in range(matrix_size)]
  for i in range(matrix_size):
    for j in range(i+1,matrix_size):
      dist_matrix[i][j] = calculate_distance(location_list[i],location_list[j])
      dist_matrix[j][i] = dist_matrix[i][j]
  return dist_matrix

def find_optimal(dist_matrix,day):
  print("dist matrix : ",dist_matrix)
  total_dist = [0]*day
  visit_result = [[] for _ in range(day)]
  for i in range(day):
    start = i
    visit = [False] * day
    visit[i] = True    
    now = i
    min_dist = 100
    min_idx = 999
    visit_result[i].append(now)
    while False in visit: #모든 클러스터를 방문할때까지
      for idx, dist in enumerate(dist_matrix[now]):
        if visit[idx] == True:
          continue
        else:
          if dist < min_dist:
            min_idx = idx
            min_dist = dist
      print("min idx, min_dist : ",min_idx,min_dist)
      
      total_dist[i] += min_dist
      now = min_idx
      visit[now] = True
      visit_result[i].append(now)
      min_dist=999
    print("total_dist : ",total_dist[i])

  shortest_cluster = np.array(total_dist).argsort()[0]
  return visit_result[shortest_cluster]
  
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
  
  cluster_center = kmeans.cluster_centers_
  for i in range(day):
    cluster_center[i][0] = i
  print(cluster_center)
  dist_matrix = make_dist_matrix(cluster_center)
  optimal_cluster_order = find_optimal(dist_matrix,day)

  for idx, label in enumerate(kmeans.labels_):
    now = save_id[idx]
    result[label].append(int(now))
  #이제 원래의 Idx와 중심좌표를 기준으로 
  new_result = []
  for i in optimal_cluster_order:
    new_result.append(result[i])
  return new_result
  
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