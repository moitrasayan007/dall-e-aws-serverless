import os
import json
import openai
import boto3
import requests
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError

# Generate a version 4 UUID
uuid_value = uuid.uuid4()

# Initialize a DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# This should be your DynamoDB table name
table = dynamodb.Table('dall-e')

# Upload the image to an S3 bucket
s3 = boto3.client('s3')

secret_name = "stage/api/openai"
region_name = "us-east-1"

# Create a Secrets Manager client
session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name
)

def get_secret():

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    print(secret)
    return json.loads(secret)


def lambda_handler(event, context):
    # Get variables from parameters
    message = event['message']

    # Call the OpenAI Image generation endpoint
    #openai.api_key = os.getenv("openai_api_key")
    secret = get_secret()

    # Extract the value of openai_api_key
    openai.api_key = secret.get('openai_api_key')
    #openai.api_key = get_secret()
    response = openai.Image.create(
        prompt=message,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    # Download the image
    image_data = requests.get(image_url).content
    

    try:
        s3_upload_path = f'{uuid_value}.png'
        s3_bucket = os.getenv("s3_bucket")  # replace with your bucket name
        s3.put_object(Bucket=s3_bucket, Key=s3_upload_path, Body=image_data, ContentDisposition='inline', ContentType='image/png')
    except NoCredentialsError:
        return {
            'statusCode': 500,
            'body': json.dumps("Missing S3 credentials")
        }

    # Generate a pre-signed URL for the uploaded object
    try:
        presigned_url = s3.generate_presigned_url('get_object', Params={'Bucket': s3_bucket, 'Key': s3_upload_path}, ExpiresIn=3600)
        
        # Save to DynamoDB
        table.put_item(
           Item={
                'prompt': message,
                'timestamp': datetime.now().isoformat(),
                'image_url': presigned_url,
                'id': str(uuid_value)  # generate a unique id
            }
        )
        
    # Return the pre-signed URL
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error in generating pre-signed url: {str(e)}")
        }
    return {
        'statusCode': 200,
        'body': json.dumps({"image_url": presigned_url})
    }