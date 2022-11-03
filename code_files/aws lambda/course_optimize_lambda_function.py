import json
import psycopg2
import os 
import math
import numpy as np
from haversine import haversine
from itertools import combinations
JEJU_AIRPORT = (0,33.5059364, 126.4959513)


def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db
  
#계산량이 너무 많을때 단순한 방법으로 경로를 나눠주는 함수
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

#여행지id를 바탕으로 위치정보를 불러오는 함수
def load_places_location(db, place_list):
  cursor = db.cursor()
  place_list = str(tuple(place_list))
  print("place list : ",place_list)
  sql = f"select place_id, latitude, longitude from places where place_id in {place_list}"
  cursor.execute(sql)
  result = cursor.fetchall()
  result = list(map(list,result))
  return result

#두 좌표간 거리 계산  
def calculate_distance_haversine(A,B):
  A_x = A[1]
  A_y = A[2]
  B_x = B[1]
  B_y = B[2]
  dist = haversine((A_x,A_y),(B_x,B_y))
  return dist

#거리 matrix를 만드는 함수
def make_dist_matrix_haversine(location_info):
  print("making matrix!!!")
  matrix_size = len(location_info)
  #initialize empty n*n matrix
  dist_matrix = [([0] * matrix_size) for _ in range(matrix_size)]
  for i in range(matrix_size):
    for j in range(i+1,matrix_size):
      dist_matrix[i][j] = calculate_distance_haversine(location_info[i],location_info[j])
      dist_matrix[j][i] = dist_matrix[i][j]
  return dist_matrix
  
#경로최적화 함수
def optimize_course(place_list,day,db):
  place_info = load_places_location(db, place_list)
  save_id = []  
  result = [[] for _ in range(day)]
  
  AIRPORT = (33.5059364,126.4959513)
  length = len(place_list)
  total_dist = [0]*length
  visit_result = [[] for _ in range(length)]

  dist_matrix = make_dist_matrix_haversine(place_info)

  for i in range(length):
    start = i
    end = 999
    visit = [False] * length
    visit[i] = True    
    now = i
    min_dist = 100
    min_idx = 999
    visit_result[i].append(now)
    print("start : ",start)
    while False in visit: #모든 클러스터를 방문할때까지
      for idx, dist in enumerate(dist_matrix[now]):
        if visit[idx] == True:
          continue
        else:
          if dist < min_dist:
            min_idx = idx
            min_dist = dist
      #print("dist from %d to %d : %.2f  "%(now,min_idx,min_dist))
      
      total_dist[start] += min_dist
      now = min_idx
      visit[now] = True
      visit_result[start].append(now)
      min_dist=999
      end = min_idx

    airport_to_start = haversine(AIRPORT,place_info[start][1:]) # 공항에서 시작지점 까지 거리
    end_to_airport = haversine(AIRPORT,place_info[end][1:]) #마지막지점에서 공항 가는 거리
    total_dist[i] += airport_to_start 
    total_dist[i] += end_to_airport  

    print("airport - 시작지점(%s) 까지 거리%s 합산"%(start,airport_to_start))
    print("끝지점(%s) - 공항  까지 거리%s 합산"%(end,end_to_airport))
    print("total_dist : ",total_dist[i])

  shortest_cluster = np.array(total_dist).argsort()[0]
  result_index = visit_result[shortest_cluster]  #최단거리를 보장하는 index 방문 순서 마지막에 이 인덱스랑 Id랑 매핑해줘야함.
 

  #day dividing ...
  day_dividing = []
  print('len(place_info)',len(place_info))
  print("result_index : ",result_index)
  
  num_comb= math.comb(len(place_info),day-1)
  print('조합 개수',num_comb)
  if num_comb > 1e5 or len(place_info)<day:
    print("조합이 너무 많으니까 path divider로 단순하게 나눌거에요~ ㅎㅎ")
    final_result = path_divider(day,result_index)
    final_result2 = []
    for i in final_result:
      tmp_list = []
      print("i : ",i)
      for j in i:
        print("j : ",j)
        tmp_list.append(place_info[j][0])
      final_result2.append(tmp_list)
    return final_result2

  for comb in combinations(result_index,day-1):
    #comb : (5,3,7)
    #print("comb : ",comb)
    if comb[-1] == result_index[-1]: 
      continue
    dist = 0
    for now in comb:
      next = result_index[result_index.index(now) + 1]
      now_loc = place_info[now][1:]
      next_loc = place_info[next][1:]
      
      dist += haversine(now_loc,next_loc)
    day_dividing.append((dist,comb))
    
  day_dividing.sort(reverse = True) #내림차순 정렬
  print('day_dividing : ',day_dividing)
  
  
  for i in range(len(day_dividing)):
    divider = day_dividing[i][1]
    pass_token = 1
    print("divider : ",divider)
    
    final_result = []
    start = 0
    for i in divider:
      cut = result_index.index(i)  
      final_result.append(result_index[start:cut+1])
      if cut-start > 5: # 하루에 6곳 이상을 방문하는 경우
        pass_token = 0
        break
      start = cut+1

    if pass_token == 0:
      continue
    
    final_result.append(result_index[start:])
  

  #index -> id 전환
    final_result2 = []
    for i in final_result:
      tmp_list = []
      print("i : ",i)
      for j in i:
        print("j : ",j)
        tmp_list.append(place_info[j][0])
      final_result2.append(tmp_list)




    return final_result2

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

  result = optimize_course(place_list,day,db)
  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "result" : result,
                            })
  }