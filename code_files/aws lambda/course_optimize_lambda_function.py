import json
import psycopg2
from sklearn.cluster import KMeans
import os 
import math
import numpy as np

JEJU_AIRPORT = (0,33.5059364, 126.4959513)

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

def find_cluster_near_airport(cluster_info,airport):
  min = 9999
  cluster_num = -1 #공항에서 가장 가까운 클러스터 번호
  for val in cluster_info:
    new_dist = calculate_distance(val,airport)
    
    if min > new_dist:
      print("min : ",new_dist)
      print("cluster_info: ",val)
      min = new_dist
      cluster_num = val[0]
  return cluster_num
  
def find_optimal(dist_matrix,day,first_day):
  print("dist matrix : ",dist_matrix)
  total_dist = [0]*day
  visit_result = []
  
  #1일차가 될 클러스터는 공항에서 가장 가까운곳으로 선정. 다음 2일차, 3일차는 now에서 가장 가까운곳으로 선정
  
  start = first_day
  visit = [False] * day
  visit[start] = True    
  now = start
  visit_result.append(now)
  min_dist = 9999
  min_idx = -1
  #visit_result[i].append(now)
  while False in visit: #모든 클러스터를 방문할때까지
    #인접한 모든 클러스터를 방문후에 가장 가까운 클러스터 택 1
    for idx, dist in enumerate(dist_matrix[now]):
      if visit[idx] == True:
        continue
      else:
        if dist < min_dist:
          min_idx = idx
          min_dist = dist
    print("min idx, min_dist : ",min_idx,min_dist)

    now = min_idx
    visit[now] = True
    visit_result.append(now)
    min_dist=999
   
  return visit_result
  
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
  
  #각 클러스터별 중심좌표를 이용해 n*n matrix 만들기
  dist_matrix = make_dist_matrix(cluster_center)
  #첫 날은 공항에서 가장 가까운 곳으로
  first_day =  int(find_cluster_near_airport(cluster_center,JEJU_AIRPORT))
  print("first day : ",first_day)
  #클러스터간 방문 순서는 거리 기준으로 최적화하기
  optimal_cluster_order = find_optimal(dist_matrix,day,first_day)

  for idx, label in enumerate(kmeans.labels_):
    now = save_id[idx]
    result[label].append(int(now))
  print("\nresult : ",result)
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