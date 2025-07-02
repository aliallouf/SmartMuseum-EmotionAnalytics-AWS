import json
import boto3
import os
import time
from datetime import datetime

# Initialize AWS services
sns_client = boto3.client('sns')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:eu-north-1:984158813029:EmotionAlerts')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'emotion-detection-data-18-june')
emotion_table = dynamodb.Table('EmotionDetectionDB')

print('Loading function')

# Global variables for latency
latency_accumulator = []
last_latency_log_time = time.time()

def process_emotion_data(artwork_id, emotion_id, detected_at, confidence, latency=None):

    result = {
        'artwork_id': artwork_id,
        'emotion_id': emotion_id,
        'detected_at': detected_at,
        'confidence': confidence
    }
    if latency is not None:
        result['latency'] = latency
    return result

# def store_raw_data_to_s3(data):

#     artwork_id = data.get('artwork_id')
#     detected_at = data.get('detected_at', time.time())
    
#     try:
#         if isinstance(detected_at, str):
#             # Check if the timestamp is a string or a Unix timestamp
#             try:
#                 detected_dt = datetime.fromisoformat(detected_at)
#             except Exception:
#                 try:
#                     detected_dt = datetime.strptime(detected_at, "%Y-%m-%d %H:%M:%S.%f")
#                 except Exception:
#                     try:
#                         detected_dt = datetime.strptime(detected_at, "%Y-%m-%d %H:%M:%S")
#                     except Exception:
#                         print(f"Error parsing detected_at: {detected_at}")
#                         raise
#             detected_at_for_key = int(detected_dt.timestamp())
#             date_str = detected_dt.strftime('%Y-%m-%d')
#         else:
#             # If already a timestamp, just convert
#             detected_at_for_key = int(detected_at)
#             date_str = datetime.fromtimestamp(detected_at_for_key).strftime('%Y-%m-%d')
#     except Exception as e:
#         # Use current time if parsing fails
#         print(f"Parsing detected_at failed: {e}, value: {detected_at}")
#         detected_at_for_key = int(time.time())
#         date_str = datetime.fromtimestamp(detected_at_for_key).strftime('%Y-%m-%d')

#     s3_key = f"raw_data/{artwork_id}/{date_str}/{detected_at_for_key}.json"

#     try:
#         s3_client.put_object(
#             Bucket=S3_BUCKET_NAME, 
#             Key=s3_key, 
#             Body=json.dumps(data)
#         )
#         print(f"Successfully stored raw data to S3: s3://{S3_BUCKET_NAME}/{s3_key}")
#     except Exception as e:
#         print(f"Error storing data to S3: {e}")

def store_data_in_dynamodb(data):
    try:
        item = {
            'artwork_id': data['artwork_id'],
            'emotion_id': data['emotion_id'],
            'timestamp': data['detected_at'],
            'confidence': data['confidence']
        }
        emotion_table.put_item(Item=item)
        print(f"Successfully stored item in DynamoDB: {item}")
    except Exception as e:
        print(f"Error storing data in DynamoDB: {e}")

def log_latency(latency):
    print(f"[LAG_METRIC] Latency: {latency:.3f} seconds")
    # Send latency in milliseconds
    latency_ms = latency * 1000
    if latency_ms >= 0:
        try:
            cloudwatch.put_metric_data(
                Namespace='EmotionDetection',
                MetricData=[
                    {
                        'MetricName': 'LatencyMs',
                        'Value': latency_ms,
                        'Unit': 'Milliseconds'
                    },
                ]
            )
            print("Latency metric (ms) sent to CloudWatch.")
        except Exception as e:
            print(f"Error sending latency metric to CloudWatch: {e}")

def lambda_handler(event, context):

    print("Received event: " + json.dumps(event, indent=2))

    # Arrival time on the platform (as ISO string)
    received_at_dt = datetime.now()
    received_at_str = received_at_dt.isoformat()

    # Extract data from the IoT rule payload
    artwork_id = event.get('artwork_id', 'UnknownArtwork')
    emotion_id = event.get('emotion_id', 'UnknownEmotion')
    detected_at = event.get('detected_at', received_at_str) # timestamp sent from device, default to now in ISO format
    confidence = event.get('confidence', 0)

    # Latency calculation
    latency = None
    if detected_at is not None:
        try:
            # Parse both detected_at and received_at as datetime
            if isinstance(detected_at, str):
                try:
                    detected_dt = datetime.fromisoformat(detected_at)
                except Exception:
                    try:
                        detected_dt = datetime.strptime(detected_at, "%Y-%m-%d %H:%M:%S.%f")
                    except Exception:
                        detected_dt = datetime.strptime(detected_at, "%Y-%m-%d %H:%M:%S")
            else:
                detected_dt = datetime.fromtimestamp(float(detected_at))
            latency = (received_at_dt - detected_dt).total_seconds()
            log_latency(latency)
        except Exception as e:
            print(f"Error calculating latency: {e}")

    # 1. Process the incoming data
    processed_data = process_emotion_data(artwork_id, emotion_id, detected_at, confidence, latency)

    # 2. Store the raw event data (e.g., in S3)
    #store_raw_data_to_s3(processed_data)

    # 3. Store the processed data in DynamoDB
    store_data_in_dynamodb(processed_data)