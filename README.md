# SmartMuseum-EmotionAnalytics-AWS: Cloud-Enhanced Visitor Experience

## Project Title: Cloud-Enhanced Visitor Experience: Emotion Detection and Analytics in a Smart Museum using AWS

## Description

This project develops a secure and scalable prototype for analyzing visitor engagement in a smart museum environment. It leverages the power of IoT, Edge computing, and AWS Cloud services to non-intrusively detect visitor emotions in real-time and provide actionable insights to museum curators. The system aims to transform traditional visitor measurement methods into an objective, data-driven approach, enhancing the overall museum experience and operational understanding.

## System Architecture

The system employs a robust Edge-to-Cloud architecture designed for efficiency, scalability, and privacy.

![image](https://github.com/user-attachments/assets/c1737b51-e2df-4877-9a74-b193e46a4212) 

**Key Components:**

* **Edge Device (Raspberry Pi 5):** Acts as the primary data collection point. It runs a custom Convolutional Neural Network (CNN) for real-time emotion detection from a connected camera. This local processing ensures immediate feedback and enhances visitor privacy by anonymizing data before transmission.
* **AWS IoT Core:** Securely ingests anonymized emotion metrics from the edge devices using the lightweight MQTT protocol.
* **AWS Lambda:** Serverless functions triggered by IoT Core messages or scheduled events for data processing, storage, and analytics.
* **Amazon DynamoDB:** A NoSQL database used to store the processed emotion data (artwork ID, emotion ID, timestamp, confidence, latency).
* **Amazon CloudWatch:** Monitors system performance and visualizes aggregated emotion statistics (e.g., total emotions per artwork, busiest hours).
* **Amazon SNS (Simple Notification Service):** Delivers daily reports and alerts to curators via email, summarizing key insights like most crowded hours and negative emotion detections.

## Features

* **Real-time Emotion Detection:** Utilizes a custom CNN model on a Raspberry Pi 5 for on-device, low-latency emotion inference.
* **Secure Data Ingestion:** Anonymized emotion metrics are securely transmitted from the edge to AWS IoT Core via MQTT.
* **Scalable Data Storage:** Processed data is stored in Amazon DynamoDB, a highly available and scalable NoSQL database.
* **Automated Analytics:** AWS Lambda functions perform daily aggregations to identify total emotions per artwork and busiest hours.
* **CloudWatch Monitoring:** Visualizes key performance indicators and aggregated emotion statistics for easy insights.
* **Daily Email Reports:** Sends automated email summaries of visitor engagement (e.g., most crowded hour, negative emotion trends) via Amazon SNS.
* **Latency Measurement:** Tracks end-to-end data transmission and processing latency from edge to cloud.
* **Privacy-Preserving:** Processes raw video data locally on the edge device; only anonymized metrics are sent to the cloud.

## Setup Guides

Follow these instructions to set up the Edge device and deploy the AWS backend components.

### 1. Edge Device Setup (Raspberry Pi)

This section guides you through setting up your Raspberry Pi 5 to run the emotion detection and data sending scripts.

**Prerequisites:**

* Raspberry Pi 5 with Raspberry Pi OS installed.
* Compatible USB camera or Raspberry Pi Camera Module.
* Stable internet connection.
* AWS IoT Core device certificate, private key, and root CA. (You'll need to generate these in the AWS IoT Core console when you register your device).

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/aliallouf/smart-museum-emotion-recognition.git](https://github.com/aliallouf/smart-museum-emotion-recognition.git)
    cd smart-museum-emotion-recognition/edge_device
    ```

2.  **Install system dependencies:**
    Ensure you have `ffmpeg` and `libatlas-base-dev` for OpenCV and TensorFlow compatibility.
    ```bash
    sudo apt update
    sudo apt install -y build-essential cmake pkg-config
    sudo apt install -y libjpeg-dev libpng-dev libtiff-dev
    sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
    sudo apt install -y libxvidcore-dev libx264-dev
    sudo apt install -y libfontconfig1-dev libcairo2-dev
    sudo apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
    sudo apt install -y libgtk2.0-dev libgtk-3-dev
    sudo apt install -y libhdf5-dev libatlas-base-dev gfortran
    sudo apt install -y python3-dev python3-pip
    ```

3.  **Create a Python Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Python dependencies:**
    Navigate to the `edge_device` directory and install the required Python packages.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Place your trained model:**
    Ensure your trained CNN model file (e.g., `your_model_name.h5`) is located in the `edge_device/` directory alongside `detect_emotions.py`.

6.  **Configure AWS IoT Core credentials:**
    * Place your AWS IoT Core device certificate (`device.pem.crt`), private key (`private.pem.key`), and Amazon Root CA (`AmazonRootCA1.pem`) in the `edge_device/certs/` directory (you'll need to create this folder: `mkdir certs`).
    * Edit `send_emotion_data.py` (and potentially `detect_emotions.py`) to configure your AWS IoT endpoint and client ID.
        *You'll need to replace placeholders with your actual AWS IoT Core endpoint, client ID, and certificate paths.*

7.  **Run the emotion detection script:**
    ```bash
    python3 detect_emotions.py
    ```
    *(Note: This assumes `detect_emotions.py` is your main script for running inference and sending data. You'll need to ensure this script correctly loads your model, captures frames, performs detection, and calls `send_emotion_data.py`.)*

### 2. AWS Backend Deployment

This section outlines the manual deployment process for your AWS Lambda functions and related services. For a more automated approach, consider using AWS SAM or CloudFormation templates (see "Deployment Scripts/Templates" below).

**Prerequisites:**

* An AWS account.
* AWS CLI configured with appropriate permissions.
* Basic understanding of AWS Lambda, DynamoDB, IoT Core, CloudWatch, and SNS.

**Steps:**

1.  **Create DynamoDB Table:**
    * Go to the DynamoDB service in the AWS Console.
    * Create a new table named `EmotionDetectionDB`.
    * Set the Primary key to `id` (String). (You might need to add a sort key like `timestamp` if your queries require it, but for a simple scan, `id` as primary key is sufficient).
    * Ensure on-demand capacity or provisioned capacity is set appropriately for your expected load.

2.  **Create SNS Topic:**
    * Go to the SNS service in the AWS Console.
    * Create a new Standard topic (e.g., `EmotionAlerts`).
    * Create a subscription to this topic for your email address to receive reports. Confirm the subscription via the email link.
    * Make a note of the Topic ARN (e.g., `arn:aws:sns:eu-north-1:ACCOUNT_ID:EmotionAlerts`). You'll need this for your Lambda functions.

3.  **Deploy AWS Lambda Functions:**

    For each Python file in `lambda_functions/` (`input_store_data.py`, `emotion_stats.py`, `hour_stats.py`, `trigger_sns.py`):

    * **Create a new Lambda function:**
        * Choose "Author from scratch".
        * **Function name:** Use a descriptive name (e.g., `InputStoreDataLambda`, `EmotionStatsLambda`, `HourStatsLambda`, `TriggerSNSLambda`).
        * **Runtime:** Python 3.9 (or newer compatible version).
        * **Architecture:** `arm64` (Graviton2) for cost efficiency, or `x86_64`.
        * **Execution role:** Create a new role with basic Lambda permissions. You will modify this role's policy in the next step.

    * **Configure Lambda Role Permissions:**
        For each Lambda function's IAM role, attach the necessary policies:
        * **`InputStoreDataLambda`:**
            * `AmazonDynamoDBFullAccess` (or more granular `PutItem` on `EmotionDetectionDB`)
            * `AWSIoTDataAccess` (for accessing IoT Core events)
            * `CloudWatchPutMetricData` (for logging latency)
            * `AmazonS3FullAccess` (if you uncomment and use S3 storage in `input_store_data.py`)
        * **`EmotionStatsLambda`:**
            * `AmazonDynamoDBReadOnlyAccess` (or more granular `Scan` on `EmotionDetectionDB`)
            * `CloudWatchPutMetricData`
        * **`HourStatsLambda`:**
            * `AmazonDynamoDBReadOnlyAccess` (or more granular `Scan` on `EmotionDetectionDB`)
            * `CloudWatchPutMetricData`
        * **`TriggerSNSLambda`:**
            * `AmazonDynamoDBReadOnlyAccess` (or more granular `Scan` on `EmotionDetectionDB`)
            * `AmazonSNSFullAccess` (or more granular `Publish` on your specific SNS Topic ARN)

    * **Upload Code:**
        * Compress the Python file (`.py`) for each Lambda function into a `.zip` file.
        * Upload the `.zip` file to the Lambda function.
        * Set the **Handler** to `your_filename.lambda_handler` (e.g., `input_store_data.lambda_handler`).

    * **Configure Environment Variables:**
        For `input_store_data.py` and `trigger_sns.py`, set the `SNS_TOPIC_ARN` environment variable to the ARN of the SNS topic you created earlier.
        ```
        SNS_TOPIC_ARN: arn:aws:sns:eu-north-1:984158813029:EmotionAlerts
        ```
        *(Update the ARN with your actual AWS account ID and region).*
        For `input_store_data.py`, if you enable S3 storage, also set `S3_BUCKET_NAME`.

4.  **Configure AWS IoT Core Rule:**
    * Go to AWS IoT Core service in the AWS Console.
    * Under "Message routing", go to "Rules".
    * Create a new rule (e.g., `EmotionDataToLambda`).
    * **Rule query statement:** `SELECT artwork_id, emotion_id, detected_at, confidence, clientid() as client_id, timestamp() as received_at FROM 'rpi5/emotion/data'`
        * *(Ensure the topic `rpi5/emotion/data` matches the `topic` variable in your `send_emotion_data.py`)*
    * **Set one or more actions:**
        * Add action: "Send a message to a Lambda function".
        * Select the `InputStoreDataLambda` function you created.
        * Make sure IoT Core has permission to invoke the Lambda function. If not, click "Grant access".

5.  **Schedule Lambda Functions with CloudWatch Events (EventBridge):**
    * Go to the EventBridge (formerly CloudWatch Events) service in the AWS Console.
    * Create a new rule.
    * Choose "Schedule" and set a fixed rate (e.g., `rate(1 day)`) for your daily analytics.
    * **Target:** Select your `EmotionStatsLambda`, `HourStatsLambda`, and `TriggerSNSLambda` functions. This will trigger them daily to perform their respective tasks.

6.  **Set up CloudWatch Dashboards (Optional but Recommended):**
    * Go to CloudWatch service.
    * Create a new dashboard.
    * Add widgets to visualize the metrics published by `emotion_stats.py` (`EmotionCountPerArtwork2`) and `hour_stats.py` (`BusiestHourCount`). You can also add metrics for Lambda invocations, errors, and duration.

## Usage

Once deployed:

1.  Ensure your Raspberry Pi with the emotion detection script (`detect_emotions.py`) is running and connected to the internet. It will continuously detect emotions and send data to AWS IoT Core.
2.  The `InputStoreDataLambda` will ingest and store this data in DynamoDB.
3.  Daily, the `EmotionStatsLambda` and `HourStatsLambda` will compute aggregate statistics and publish them to CloudWatch.
4.  Daily, the `TriggerSNSLambda` will query DynamoDB, generate a summary report, and send it to the email subscribed to your SNS topic.
5.  Monitor your CloudWatch dashboards for real-time insights and system health.

## Technologies Used

* **Python 3.x**
* **TensorFlow/Keras:** For building and running the custom CNN emotion detection model.
* **OpenCV:** For camera interaction and image processing on the Raspberry Pi.
* **AWSIoTPythonSDK:** For MQTT communication from the edge device to AWS IoT Core.
* **Boto3:** AWS SDK for Python, used by Lambda functions to interact with AWS services.
* **AWS IoT Core:** Managed cloud service that lets connected devices easily and securely interact with cloud applications and other devices.
* **AWS Lambda:** Serverless compute service for running backend code.
* **Amazon DynamoDB:** Fully managed, high-performance NoSQL database service.
* **Amazon CloudWatch:** Monitoring and observability service for AWS resources and applications.
* **Amazon SNS (Simple Notification Service):** Fully managed messaging service for application-to-application (A2A) and application-to-person (A2P) communication.
* **Raspberry Pi 5:** Edge computing device for on-site emotion detection.
* **MQTT:** Lightweight messaging protocol for IoT devices.
