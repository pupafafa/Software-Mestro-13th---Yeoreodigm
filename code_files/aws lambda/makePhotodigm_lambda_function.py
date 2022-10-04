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

frame_coordinate = {1:(33,323,110,473),2:(33,323,110,473),3:(47,652,101,516),4:(47,652,101,516)}
frame_inner_size = {1: (261,340),2:(261,340),3:(509,407),4:(509,407)}
frame_num_indicator = {(620,920):1,(1206,971):3 }

def connect_s3():
  return boto3.client('s3',aws_access_key_id=os.environ['ACCESS_KEY_ID'],
                                  aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'],
                                  region_name=os.environ['REGION'])
    
#img_type : frame,image,photoDigm
def load_image(client,img_type,file_name):
  bucket_name = "yeoreodigm-s3"
  prefix = prefix_info[img_type]

  
  entire_path = prefix + file_name  #디렉토리 경로를 모두 포함한 파일 경로
  print(entire_path)
  result = client.list_objects(Bucket = bucket_name, Prefix=entire_path)

  for obj in result.get('Contents'):
    data = client.get_object(Bucket=bucket_name,Key=obj.get('Key'))
    data_content = data['Body'].read()
    #display(Image.open(io.BytesIO(data_content)))
    return Image.open(io.BytesIO(data_content))
    
    
    
def lambda_handler(event, context):
  try:
    # TODO implement
    img1 = event['img1']
    img2 = event['img2']
    img3 = event['img3']
    img4 = event['img4']
    frame = event['frame']
    key = event['key']
    print(event)
    print(context)
    
    client = connect_s3()
    print("client connection success!!")
    frame_num=0
    if 'frame' in frame:
      print("this is frame")
      frame_img = load_image(client=client,img_type='frame',file_name=frame) 
      print("loaed frame successfully!!")
      frame_size = frame_img.size
      print("frame_size : ", frame_size)
      frame_num = frame_num_indicator[frame_size]
    else:
      #1. 포토다임을 파일 이름으로 로드하기
      print("this is photodigm edit section")
      frame_img = load_image(client=client,img_type='photoDigm',file_name=frame) 
      print("loaed photoDigm successfully!!")
      frame_size = frame_img.size
      frame_num = frame_num_indicator[frame_size]
      print("frame_size : ", frame_size)
      
  
    x1,x2,y1,y2 = frame_coordinate[frame_num]
    inner_size = frame_inner_size[frame_num]

  
    if img1 != None:
      img1 = load_image(client=client,img_type='image',file_name=img1).resize(inner_size)
      frame_img.paste(img1,(x1,y1))
    if img2 != None:
      img2 = load_image(client=client,img_type='image',file_name=img2).resize(inner_size)
      frame_img.paste(img2,(x2,y1))
    if img3 != None:
      img3 = load_image(client=client,img_type='image',file_name=img3).resize(inner_size)
      frame_img.paste(img3,(x1,y2))
    if img4 != None:
      img4 = load_image(client=client,img_type='image',file_name=img4).resize(inner_size)
      frame_img.paste(img4,(x2,y2))
    
    print("loaded image files and process done!!")
    
    
    mem_out = io.BytesIO()
    frame_img.save(mem_out,format=frame_img.format) # binary data를 BytesIO로 변환해서 memout에 담기
    mem_out.seek(0)#파일포인터(?) 복구
    bucket_name = 'yeoreodigm-s3'
    save_path = prefix_info['photoDigm'] + key
    
    client.upload_fileobj(mem_out,bucket_name,save_path,ExtraArgs={'ContentType':"image/png"})
    
      
    print("image upload done!!")
  
    return {
        'statusCode': 200,
        'body': json.dumps("everything done!!"),
    }
  
  except:
    print("except!!! ")
    raise Exception('Invalid file path ...')

