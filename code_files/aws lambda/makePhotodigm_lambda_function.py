import json
from PIL import Image
import boto3
import psycopg2
import os
import io

prefix_info = {
  'image' : "assets/photoDigm/userPicture/",
  'frame' : "assets/photoDigm/frame/",
  'photoDigm' : "assets/photoDigm/photoDigm/",
}

def connect_s3():
  return boto3.client('s3',aws_access_key_id="AKIA3K5IYMAM2GOIJ3FL",
                                  aws_secret_access_key="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",
                                  region_name="ap-northeast-2")
    
#img_type : frame,image,photoDigm
def load_image(client,img_type,file_name):
  bucket_name = "yeoreodigm-s3"
  prefix = prefix_info[img_type]

  
  entire_path = prefix + file_name  #디렉토리 경로를 모두 포함한 파일 경로
  result = client.list_objects(Bucket = bucket_name, Prefix=entire_path)

  for obj in result.get('Contents'):
    data = client.get_object(Bucket=bucket_name,Key=obj.get('Key'))
    data_content = data['Body'].read()
    #display(Image.open(io.BytesIO(data_content)))
    return Image.open(io.BytesIO(data_content))
    
    
    
def lambda_handler(event, context):
  # TODO implement
  img1 = event['img1']
  img2 = event['img2']
  img3 = event['img3']
  img4 = event['img4']
  frame = event['frame']
  key = event['key']
  
  client = connect_s3()
  
  try:
    frame_img = load_image(client=client,img_type='frame',file_name=frame) 
    img1 = load_image(client=client,img_type='image',file_name=img1).resize((260,340))
    img2 = load_image(client=client,img_type='image',file_name=img2).resize((260,340))
    img3 = load_image(client=client,img_type='image',file_name=img3).resize((260,340))
    img4 = load_image(client=client,img_type='image',file_name=img4).resize((260,340))
  except:
      return {
      'statusCode': 400,
      'body': json.dumps('Failed to Load Image from s3!'),

  }
  x1 = 34
  x2 = 322
  y1 = 110
  y2 = 472
  
  frame_img.paste(img1,(x1,y1))
  frame_img.paste(img2,(x2,y1))
  frame_img.paste(img3,(x1,y2))
  frame_img.paste(img4,(x2,y2))
  
  mem_out = io.BytesIO()
  frame_img.save(mem_out,format=frame_img.format) # binary data를 BytesIO로 변환해서 memout에 담기
  mem_out.seek(0)#파일포인터(?) 복구
  bucket_name = 'yeoreodigm-s3'
  save_path = prefix_info['photoDigm'] + key
  client.upload_fileobj(mem_out,bucket_name,save_path)
  
  return {
      'statusCode': 200,
      'body': json.dumps('Hello from Lambda!'),
      
      
      
  }
