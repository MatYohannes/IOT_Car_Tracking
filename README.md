# System Architecture

## Sources
-   Vehicle information from location A to location B
-   GPS information for accuracy
-   Camera snapshots from vehicle. Dummy photos
-   Weather information
-   Emergency information for accidents, etc.

## Docker Container
-   Run Kafka with Zookeeper, mutiple brokers
-   Apache Spark is the consumer

## Downstream
-   Stream raw data from Spark to S3 bucket
-   Write condition with AWS Glue to extract information from raw data in S3 using data catalog
-   AWS IAM will control AWS services
-   Endpoints can be AWS Redshift or AWS Athena

## Visualization
-   PowerBI
-   Tableau
-   Other options such as Apache Preset, Metabase


## Step Up
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

## Packages
1. pip install confluent-kafka simplejson pyspark
NOTE: If you have issues with pip, delete the venv and recreate it, then pip install
2. pip freeze > requirements.txt

## main.py



## Docker Desktop
1. When main.py is running, to see the topics [vehicle_data, gps_data, emergency_data, traffic_data, weather_data], in Docker desktop, do the following.
    a. Select the broker container
    b. Got to 'Exec'
    c. run 'kafka-topics --list --bootstrap-server broker:29092 . This will list the topics you have in your code that was pushed to Kafka.
    d. To review the data produced in each topic, run 'kafka-console-consumer --topic <topic name> --bootstrap-server broker:9092 --from-beginning

# AWS Services
## S3
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

## spark-city.py
1. To view spark web UI, go to Docker Desktop, select spark-master-1, go to ports, select 'Show all ports', and select '9090:8080'. '7077:7077' is the spark master url where we are submitting our spark jobs.
    a. Here you will be able to see the workers
2. For streaming, the spark .config will need a Kafka jar from the Maven Repo.
    a. https://mvnrepository.com/
    b. Search for sql-kafka
    c. Select version to match your pyspark. Check your requirements file for version number.
    c. Copy the group id under the Maven tab. Example: <groupId>org.apache.spark</groupId>
    d. For the .config("spark.jars.packages", "org.apache.spark")
    e. Copy the artifactId. Example: <artifactId>spark-sql-kafka-0-10_2.13</artifactId>
    f. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13"
    g. Copy the version: <version>3.5.4</version>
    h. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.4"
3. We will need a package for AWS from the Maven Repo.
    a. https://mvnrepository.com/
    b. Search for hadoop-aws
    c. Select an older version with higher Usages count.
    d. Under the Maven tab, copy the groupId, artifactId, and version.
    e. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.4",
            "org.apache.hadoop:hadoop-aws:3.3.4"
4. We will need a package for the AWS java sdk from Maven Repo.
    a. https://mvnrepository.com/
    b. Search for aws-java-sdk
    c. Select an older version with higher Usages count over 10.
    d. Under the Maven tab, copy the groupId, artifactId, and version.
    e. Add to .config: "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.4",
            "org.apache.hadoop:hadoop-aws:3.3.4",
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
        --packages org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.4,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk:1.11.534 \
        jobs/spark-city.py