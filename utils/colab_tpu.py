from google.colab import auth
import tensorflow as tf
import os, json

TPU_ADDRESS = f'grpc://{os.environ["COLAB_TPU_ADDR"]}'

def setup_gcs():
  auth.authenticate_user()
  with tf.Session(TPU_ADDRESS) as sess:
    with open('/content/adc.json', 'r') as f:
      auth_info = json.load(f)
    tf.contrib.cloud.configure_gcs(sess, credentials=auth_info)