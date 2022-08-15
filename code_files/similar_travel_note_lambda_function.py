import psycopg2
import json
import random
import os

def load_db():
  endpoint = os.environ['END_POINT']
  dbname = os.environ['DB_NAME']
  user = os.environ['USER_NAME']
  password = os.environ['WONSEOK']
  db = psycopg2.connect(host=endpoint,dbname=dbname,user=user,password=password)
  return db

def find_similart_note(travel_note_id,num_of_result,db):
  #db에서 travel_note_id를 이용, course_로 들어가서 클러스터 확인 후 동일 클러스터 내에서 length나 day가 비슷한걸로 4개 추천해주면 됨.
  cursor = db.cursor()
  coures_id = travel_note_id
  length_sql = f"SELECT length FROM course_ where id = {travel_note_id}"
  cursor.execute(length_sql)
  length = cursor.fetchone()[0]

  sql = f"SELECT id FROM course_ where cluster = (SELECT cluster FROM course_ where id = {travel_note_id}) and length>{length-2} and length<{length+2}"
  cursor.execute(sql)
  result = cursor.fetchall()
  #tuple형태로 되어있는것을 value만 꺼내주기
  result = list(map(lambda x: x[0],result))
  #자기 자신은 제외
  result.remove(travel_note_id)
  count = len(result)
  if count == 0:
    return []
  if num_of_result > count:
    num_of_result = count
  
  result = random.sample(result,num_of_result)
  result = list(map(int,result))
  return result

def lambda_handler(event, context):
    # TODO implement
  travel_note_id = int(event['queryStringParameters']['travelNoteId'])
  num_of_result = int(event['queryStringParameters']['numOfResult'])
  try:
    db = load_db()
  except:
    return {
            'statusCode': 500,
            "success": False,
            "message": "Database Error",
            
            
        }
        
  similar_travel_notes = find_similart_note(travel_note_id,num_of_result,db)
  
  

  return {
      'statusCode': 200,
      'body': json.dumps({  
                            "noteList" : similar_travel_notes,
                            })
  }
