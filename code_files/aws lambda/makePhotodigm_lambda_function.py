import json
from PIL import Image, ImageOps
import boto3
import psycopg2
import os
import io

prefix_info = {
  'image' : "assets/photoDigm/userPicture/",
  'frame' : "assets/photoDigm/frame/",
  'photoDigm' : "assets/photoDigm/photoDigm/",
}

frame_coordinate = {1:((180,400),(930,190),(180,1364),(930,1154)),2:((80,155),(1068,155),(80,915),(1068,915)),3:((180,363),(930,150),(180,1327),(930,1114)),\
                      4:((90,160),(1095,160),(230,920),(1235,920)),5:((160,180),(920,180),(160,1200),(920,1200)),6:((90,160),(1095,160),(345,925),(1350,925)),\
                        7:((160,170),(920,170),(159,1190),(920,1200)),8:((34,110),(323,110),(33,473),(323,473))}

frame_inner_size = {1:(690,920),2:(960,720),3:(690,920),4:(960,720),5:(720,960),6:(960,720),7:(720,960),8: (260,340)}

def connect_s3():
  return boto3.client('s3',aws_access_key_id=os.environ['ACCESS_KEY_ID'],
                                  aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'],
                                  region_name=os.environ['REGION'])
    
#img_type : frame,image,photoDigm
def load_image(s3,img_type,file_name):
  print("load_image....")
  bucket = 'yeoreodigm-s3'
  Bucket = s3.Bucket(bucket)
  prefix = prefix_info[img_type]
  entire_path = prefix + file_name
  object_ = Bucket.Object(entire_path)
  response = object_.get()
  file_stream = response['Body']
  img = Image.open(file_stream)
  print("Successfully loaded original img")
  print("applying new process if img has rotation info")
  exif = img.getexif()
  for k in exif.keys():
    if k!=0x0112 and k!= 0x10E: # orientation information (0x0112),frame number (0x10E)
      exif[k] = None
      del exif[k]
  new_exif = exif.tobytes()
  img.info["exif"] = new_exif
  transposed_img = ImageOps.exif_transpose(img)
  print("Everything done.")
  return transposed_img

def upload_image(s3,img, img_type,key):
  bucket = 'yeoreodigm-s3'
  Bucket = s3.Bucket(bucket)
  save_path = prefix_info[img_type] + key
  print('저장경로 : ',save_path)
  object_ = Bucket.Object(save_path)

  file_stream = io.BytesIO()
  
  img.save(file_stream,format='png') # binary data를 BytesIO로 변환해서 file stream에 담기
  object_.put(Body = file_stream.getvalue(),ContentType='image/png')
  print("image upload done!!")

def make_photodigm(s3,frame, key):
    frame_img = load_image(s3=s3,img_type='frame',file_name=frame) 
    frame_num = int(frame_img.getexif()[270])

    coordinate = frame_coordinate[frame_num]
    inner_size = frame_inner_size[frame_num]

    if img1 != None:
      img1 = load_image(s3=s3,img_type='image',file_name=img1)
      img1 = ImageOps.fit(img1,inner_size)
      frame_img.paste(img1,coordinate[0])
    if img2 != None:
      img2 = load_image(s3=s3,img_type='image',file_name=img2)
      img2 = ImageOps.fit(img2,inner_size)
      frame_img.paste(img2,coordinate[1])
    if img3 != None:
      img3 = load_image(s3=s3,img_type='image',file_name=img3)
      img3 = ImageOps.fit(img3,inner_size)
      frame_img.paste(img3,coordinate[2])
    if img4 != None:
      img4 = load_image(s3=s3,img_type='image',file_name=img4)
      img4 = ImageOps.fit(img4,inner_size)
      frame_img.paste(img4,coordinate[3])

    print("Loading image files and processing is done!!")


    upload_image(s3,frame_img,'photoDigm',key=key)    

    
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
    
    print("client connection success!!")
    s3 = connect_s3()
    
    def make_photodigm(s3,frame, key)
    
  
    return {
        'statusCode': 200,
        'body': json.dumps("everything done!!"),
    }
  
  except:
    print("except!!! ")
    raise Exception('Invalid file path ...')

