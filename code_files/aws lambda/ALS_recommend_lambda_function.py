import json
import implicit
import pandas as pd
import scipy.sparse as sparse
import numpy as np
import boto3

def connect_s3():
  return boto3.resource('s3',aws_access_key_id=os.environ['ACCESS_KEY_ID'],
                                  aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'],
                                  region_name=os.environ['REGION'])


def load_file(s3,file_name):
  bucket = 'yeoreodigm-s3'
  Bucket = s3.Bucket(bucket)
  prefix = 'assets/AI_ALS'
  object_key = prefix + file_name
  file_content =boto3.resource.get_object (
      Bucket=S3_BUCKET, Key=object_key)["Body"].read()
    return file_content



def lambda_handler(event, context):
    
    member_id = int(event['queryStringParameters']['memberId'])
    
    model = implicit.als.AlternatingLeastSquares(factors=20, regularization = 0.1, iterations = 20)
    model_file = load_file(s3,"11.01_ALS_Model")
    loaded_model = model.load(model_file)
    
    matrix_file = load_file(s3,"11.01_Sparse_Matrix.npzl")
    matrix = sparse.load_npz(matrix_file)
    
    place_log_file = load_file(s3,"10.31_place_log.csv")
    place_log = pd.read_csv("/content/drive/MyDrive/yeoreodigm/data_files/10.31_place_log.csv",index_col=0)
    

    members = np.sort(place_log['member_id'].unique())
    user_id = np.where(members==2155)
    recommend, score = loaded_model.recommend(userid=user_id,user_items=matrix[user_id],N=10,filter_already_liked_items=True)
    recommend = list(map(int,recommend))
    return {
        'statusCode': 200,
        'body': recommend
    }
