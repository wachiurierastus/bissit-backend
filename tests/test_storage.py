from app.storage import upload_to_s3, download_from_s3
from config.config import config
import os

def test_upload_to_s3():
    with open('test_file.txt', 'w') as f:
        f.write('Test content')

    url = upload_to_s3('test_file.txt')
    assert url is not None
    assert url.startswith(f'https://{config.S3_BUCKET_NAME}.s3.amazonaws.com/')

    os.remove('test_file.txt')

def test_download_from_s3():
    url = 'https://your-test-bucket.s3.amazonaws.com/test_file.txt'
    download_from_s3(url, 'downloaded_file.txt')
    assert os.path.exists('downloaded_file.txt')

    with open('downloaded_file.txt', 'r') as f:
        content = f.read()
    assert content == 'Test content'

    os.remove('downloaded_file.txt')