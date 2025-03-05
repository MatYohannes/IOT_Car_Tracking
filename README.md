# IOT Car Tracking Instruction Manual

Objective:

The IoT Car Tracking System is designed to collect, process, and analyze real-time vehicle tracking data using Apache Kafka, Apache Spark, and AWS cloud services. The system captures and processes data related to vehicle locations, GPS accuracy, camera snapshots, weather conditions, and emergency events.

Outcome & Benefits:

    Real-time vehicle tracking and event monitoring.
    Scalable, cloud-based architecture for processing large data streams.
    Advanced analytics for insights into vehicle movement, traffic, and environmental conditions.
    Integration with business intelligence tools for reporting and visualization.

## System Architecture

### Sources
- Vehicle information from location A to location B
- GPS information for accuracy
- Camera snapshots from the vehicle (dummy photos)
- Weather information
- Emergency information for accidents, etc.

### Docker Container
- Run Kafka with Zookeeper, multiple brokers
- Apache Spark is the consumer

### Downstream
- Stream raw data from Spark to an S3 bucket
- Use AWS Glue to extract information from raw data in S3 using a data catalog
- AWS IAM will control AWS services
- Endpoints can be AWS Redshift or AWS Athena

### Visualization
- Power BI
- Tableau
- Other options such as Apache Superset, Metabase

## Setup Instructions

### Environment Setup
1. Use WSL for a Linux-based environment.
2. Create a virtual environment: `python3 -m venv car_tracking`
3. Activate the virtual environment: `source car_tracking/bin/activate`
4. Create a Docker configuration file: `touch docker-compose.yml`
5. Fill in the `docker-compose.yml` file.
6. Start Docker services: `docker compose up -d`
7. A `jobs` folder will be created.
8. Create the main script: `touch main.py`
    - This is where production code is written.
9. Create a Spark job script: `touch jobs/spark-city.py`
    - This script will handle Spark jobs listening to Kafka events.

### Package Installation
1. Install necessary packages: `pip install confluent-kafka simplejson pyspark`
   - If issues arise, delete and recreate the virtual environment, then reinstall.
2. Save dependencies: `pip freeze > requirements.txt`

## Running Kafka and Spark

### Docker Desktop
1. When `main.py` is running, list Kafka topics:
   - Open Docker Desktop, select the broker container.
   - Go to 'Exec' and run:
     ```sh
     kafka-topics --list --bootstrap-server broker:29092
     ```
   - This will list available topics: `vehicle_data`, `gps_data`, `emergency_data`, `traffic_data`, `weather_data`.
2. To view topic data, run:
   ```sh
   kafka-console-consumer --topic <topic_name> --bootstrap-server broker:9092 --from-beginning
   ```

## AWS Services

### S3 Bucket Setup
1. Create a bucket to collect streamed data from Kafka and Spark.
2. Ensure "Block all public access" is **disabled**.
3. Set the following bucket policy:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Principal": {
                   "AWS": "<AWS ARN from IAM>"
               },
               "Action": [
                   "s3:GetObject",
                   "s3:PutObject",
                   "s3:PutObjectAcl"
               ],
               "Resource": "arn:aws:s3:::spark-streaming-data-myy/*"
           }
       ]
   }
   ```
4. Store AWS credentials in a config file: `touch jobs/config.py`.

### Spark Streaming Setup
1. Access Spark Web UI via Docker Desktop:
   - Select `spark-master-1` > Ports > 'Show all ports'.
   - Open `9090:8080` for Spark Web UI.
   - Open `7077:7077` as Spark master URL for submitting jobs.
2. Configure Spark for Kafka and AWS:
   - Install necessary JARs from [Maven Repository](https://mvnrepository.com/):
     - `spark-sql-kafka-0-10_2.13`
     - `hadoop-aws`
     - `aws-java-sdk`
   - Add the JARs to the Spark configuration.
   - Configure AWS credentials in `spark-city.py`.
3. Define schemas for `vehicle`, `gps`, `traffic`, `weather`, and `emergency` data using `StructType`.
4. Implement a function to read Kafka topics with defined schemas.
5. Create DataFrames for each dataset.
6. Implement a function to write streaming data to S3.
7. Run the Spark job:
   ```sh
   docker exec -it iot_car_tracking-spark-master-1 spark-submit \
       --master spark://spark-master:7077 \
       --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.1,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
       jobs/spark-city.py
   ```

## AWS Glue and Athena
1. **Create AWS Glue Crawler**:
   - Name: `SmartCityDataCrawler`
   - Select the S3 bucket containing the raw data.
   - Set exclusion patterns: `_spark_metadata`, `**/_spark_metadata`, `**spark_metadata**`.
2. **Create IAM Role**: `AWSGlueServiceRole-SmartCity`
3. **Create Database**:
   - Name: `smartcity`
   - Target database for crawler output.
4. **Run the Crawler**:
   - Generates tables for `vehicle`, `gps`, `traffic`, `weather`, and `emergency` data.
5. **Query Data with Athena**:
   - Set Athena query result location: `s3://spark-streaming-data-myy/output/`
   - Execute SQL queries on the generated tables.

## Error Handling and Debugging
1. **Check Logs**:
   - Use `docker logs -f <container_name>` to monitor running services.
   - Kafka logs can be checked inside the broker container.
   - Spark job errors appear in `spark-master` logs.
2. **Re-run Services if Necessary**:
   - Restart Kafka, Spark, or any failing services with `docker compose restart <service_name>`.
3. **Check Data Flow**:
   - Verify Kafka topic data before Spark processing.
   - Ensure AWS credentials are correct for writing to S3.

---

This manual provides a step-by-step guide to setting up an IoT-based car tracking system using Docker, Kafka, Spark, AWS S3, Glue, and Athena. The data can be visualized using Power BI, Tableau, or other tools.



# Detailed step instructions below

## System Architecture

### Sources
-   Vehicle information from location A to location B
-   GPS information for accuracy
-   Camera snapshots from vehicle. Dummy photos
-   Weather information
-   Emergency information for accidents, etc.

### Docker Container
-   Run Kafka with Zookeeper, mutiple brokers
-   Apache Spark is the consumer

### Downstream
-   Stream raw data from Spark to S3 bucket
-   Write condition with AWS Glue to extract information from raw data in S3 using data catalog
-   AWS IAM will control AWS services
-   Endpoints can be AWS Redshift or AWS Athena

### Visualization
-   PowerBI
-   Tableau
-   Other options such as Apache Preset, Metabase


### Step Up
1. wsl to use linux base
2. python3 -m venv car_tracking
3. source car_tracking/bin/activate
4. touch docker-compose.yml
5. Fill in yml file.
6. docker compose up -d
7. jobs folder will be create.
8. touch main.py
    -   main.py is where we are going to be doing the production
9. touch jobs/spack-city.py
    -   spark-city.py is where we write the spark jobs that listen to events from Kafka

### Packages
1. pip install confluent-kafka simplejson pyspark  
NOTE: If you have issues with pip, delete the venv and recreate it, then pip install  
2. pip freeze > requirements.txt  

## main.py

### Docker Desktop
1. When main.py is running, to see the topics [vehicle_data, gps_data, emergency_data, traffic_data, weather_data], in Docker desktop, do the following.  
    a. Select the broker container    
    b. Got to 'Exec'  
    c. run 'kafka-topics --list --bootstrap-server broker:29092 . This will list the topics you have in your code that was pushed to Kafka.  
    d. To review the data produced in each topic, run 'kafka-console-consumer --topic <topic name> --bootstrap-server broker:9092 --from-beginning  

## AWS Services
### S3
1. Create bucket to collect streamed data from kafka and Spark.  
    a. Make sure bucket does not 'Block all public access'  
    b. Bucket policy:  
        '''   
            {  
                "Version": "2012-10-17",  
                "Statement": [  
                    {  
                        "Effect": "Allow",  
                        "Principal": {  
                            "AWS": <provide AWS arn from IAM>  
                        },  
                        "Action": [  
                            "s3:GetObject",  
                            "s3:PutObject",  
                            "s3:PutObjectAcl"  
                        ],  
                        "Resource": "arn:aws:s3:::spark-streaming-data-myy/*"  
                    }  
                ]  
            }  
        '''  
2. touch jobs/config.py . This will contain your AWS Access Key.  

### spark-city.py
1. To view spark web UI, go to Docker Desktop, select spark-master-1, go to ports, select 'Show all ports', and select '9090:8080'. '7077:7077' is the spark master url where we are submitting our spark jobs.  
    a. Here you will be able to see the workers  
2. For streaming, the spark .config will need a Kafka jar from the Maven Repo.   
    a. https://mvnrepository.com/  
    b. Search for sql-kafka  
    c. Select version to match your pyspark. Check your requirements file for version number.  
    c. Copy the group id under the Maven tab. Example: <groupId>org.apache.spark</groupId>  
    d. For the .config("spark.jars.packages", "org.apache.spark")  
    e. Copy the artifactId. Example: <artifactId>spark-sql-kafka-0-10_2.12</artifactId>  
    f. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12"  
    g. Copy the version: <version>3.5.0</version>  
    h. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"  
3. We will need a package for AWS from the Maven Repo.  
    a. https://mvnrepository.com/  
    b. Search for hadoop-aws 
    c. Select an older version with higher Usages count.  
    d. Under the Maven tab, copy the groupId, artifactId, and version.  
    e. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
            "org.apache.hadoop:hadoop-aws:3.3.1"  
4. We will need a package for the AWS java sdk from Maven Repo.  
    a. https://mvnrepository.com/  
    b. Search for aws-java-sdk  
    c. Select an older version with higher Usages count over 10.  
    d. Under the Maven tab, copy the groupId, artifactId, and version.  
    e. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.0",  
            "org.apache.hadoop:hadoop-aws:3.3.1",  
            "com.amazonaws:aws-java-sdk:1.11.534"  
5. Set up AWS configurations  
    a. .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")  
    b. Add the Access and Secret Key to have access to AWS services. Need to add "from config import configuration" to file. Package is the config.py file you created.  
        i. .config("spark.hadoop.fs.s3a.access.key", configuration.get('AWS_ACCESS_KEY'))\  
        ii. .config("spark.hadoop.fs.s3a.secret.key", configuration.get('AWS_SECRET_KEY'))\  
    c. Next add the AWS credential provider. 
        - .config('spark.hadoop.fs.s3a.aws.credentials.provider', 'org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider')  
    d. Finish it off with .getOrCreate()  
6. Add log level.  
7. Create Vehicle, gps, traffic, weather, emergency schema with StructType.  
    - Match the fieldType for field  
8. To read the data, create a function that can work with multiple schema  
    -   funciton read_kafka_topic  
        - parameters: topic, schema  
9. Create dataframes from vehicles, gps, traffic, weather, and emergency.  
10. Create function streamWriter that will write data into S3 and initiate it.  
11. To write to s3 in parallel, we do the following  
    - First clear the broker. Go to Docker when check the existing topics:  
        kafka-topics --list --bootstrap-server broker:29092  
        kafka-topics --delete --topic <names> --bootstrap-server broker:29092  
12. Run: docker exec -it iot_car_tracking-spark-master-1 spark-submit \  
        --master spark://spark-master:7077 \  
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.1,com.amazonaws:aws-java-sdk-bundle:1.12.262 \  
        jobs/spark-city.py  

## AWS Services

### AWS Glue and Athena
Now that data is uploaded to S3, we need to transform the data. We will use AWS Glue to crawl the data and create a data catalog, then link AWS Redshift and Athena. 
1. Create a **Crawler**.
    -   Name: SmartCityDataCrawler
    -   Data sources: select S3 bucket/data.
        -   Subsequent crawler runs: Crawl all sub-folders
    -   Check **Exclude files matching pattern**
        -   Exlude ***_spark_metadata***, ***"_spark_metadata/**"****, ***"**/_spark_metadata"***, ***"**spark_metadata**"***

2. Create and select IAM role "AWSGlueServiceRole-SmartCity".
3. Create database and select "smartcity" to target database.
4. Run crawler.
5. When crawler is done, go to Tables. 5 Tables would have been created.
6. Select **Table data** to view with Athena.
7. Got to Athena settings to set output location. ex. s3://spark-streaming-data-myy/output/
8. Run queries for each table

