import boto3
from botocore.exceptions import NoCredentialsError
from config.config import config

s3_client = boto3.client('s3',
                         aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                         region_name=config.AWS_DEFAULT_REGION)


def upload_to_s3(file_name, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        s3_client.upload_file(file_name, config.S3_BUCKET_NAME, object_name)
        return f"https://{config.S3_BUCKET_NAME}.s3.amazonaws.com/{object_name}"
    except NoCredentialsError:
        print("Credentials not available")
        return None


def download_from_s3(s3_url, local_filename):
    bucket = s3_url.split('/')[2].split('.')[0]
    object_name = '/'.join(s3_url.split('/')[3:])
    s3_client.download_file(bucket, object_name, local_filename)
