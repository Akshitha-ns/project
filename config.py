import os

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

USE_S3 = False  # Toggle S3 usage

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DATABASE = os.path.join(BASE_DIR, 'videos.db')
