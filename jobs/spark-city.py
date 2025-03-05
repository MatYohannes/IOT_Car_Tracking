from pyspark.sql import SparkSession, DataFrame
from config import configuration
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType, IntegerType
from pyspark.sql.functions import from_json, col



def main():
    spark = SparkSession.builder.appName("SmartCityStreaming") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
            "org.apache.hadoop:hadoop-aws:3.3.1,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.access.key", configuration.get('AWS_ACCESS_KEY')) \
    .config("spark.hadoop.fs.s3a.secret.key", configuration.get('AWS_SECRET_KEY')) \
    .config('spark.hadoop.fs.s3a.aws.credentials.provider', 
            'org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider') \
    .getOrCreate()
    
    # Adjust the log level to minimize the console output on executors
    spark.sparkContext.setLogLevel('WARN')

    # Vehicle schema
    vehicleSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("location", StringType(), True),
        StructField("speed", DoubleType(), True),
        StructField("direction", StringType(), True),
        StructField("make", StringType(), True),
        StructField("model", StringType(), True),
        StructField("year", IntegerType(), True),
        StructField("fuelType", StringType(), True)
    ])

    # GPS schema
    gpsSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("speed", DoubleType(), True),
        StructField("direction", StringType(), True),
        StructField("vehicleType", StringType(), True)
    ])

    # traffic schema
    trafficSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("cameraId", IntegerType(), True),
        StructField("location", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("snapshot", StringType(), True)
    ])

    # weather schema
    weatherSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("location", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("temperature", DoubleType(), True),
        StructField("weatherCondition", StringType(), True),
        StructField("precipitation", DoubleType(), True),
        StructField("windSpeed", DoubleType(), True),
        StructField("humidity", IntegerType(), True),
        StructField("airQualityIndex", DoubleType(), True)
    ])

    # emergency schema
    emergencySchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("incidentId", StringType(), True),
        StructField("type", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("location", StringType(), True),
        StructField("status", StringType(), True),
        StructField("description", StringType(), True)
    ])

    def read_kafka_topic(topic, schema):
        return (spark.readStream    
                .format('kafka')    # Read from Kafka as a streaming source
                .option('kafka.bootstrap.servers', 'broker:29092')  # Specify Kafka broker address 
                .option('subscribe', topic) # Subscribe to the specified topic
                .option('startingOffsets', 'earliest')  # Read from the beginning of the topic
                .load() # Load the Kafka stream
                .selectExpr('CAST(value AS STRING)')   # Convert Kafka message value to string
                .select(from_json(col('value'), schema).alias('data'))  # Parse JSON using the provided schema
                .select('data.*') # Extract fields from the parsed JSON
                .withWatermark('timestamp', '2 minutes')    # apply tag to specific window
                )

    def streamWriter(input: DataFrame, checkpointFolder, output):
        return (input.writeStream
                .format('parquet')  # Write the stream output in Parquet format
                .option('checkpointLocation', checkpointFolder)  # Define checkpoint location for fault tolerance
                .option('path', output)  # Specify output directory for storing Parquet files
                .outputMode('append')  # Append new records instead of overwriting existing data
                .start())  # Start the streaming query

    # create dataframes
    vehicleDF = read_kafka_topic('vehicle_data', vehicleSchema).alias('vehicle')
    gpsDF = read_kafka_topic('gps_data', gpsSchema).alias('gps')
    trafficDF = read_kafka_topic('traffic_data', trafficSchema).alias('traffic')
    weatherDF = read_kafka_topic('weather_data', weatherSchema).alias('weather')
    emergencyDF = read_kafka_topic('emergency_data', emergencySchema).alias('emergency')

    # join all the dataframes with id and timestamps
    # join

    query1 = streamWriter(vehicleDF, f's3a://{configuration.get('S3_BUCKET_NAME')}/checkpoints/vehicle_data',
                 f's3a://{configuration.get('S3_BUCKET_NAME')}/data/vehicle_data')
    query2 = streamWriter(gpsDF, f's3a://{configuration.get('S3_BUCKET_NAME')}/checkpoints/gps_data',
                 f's3a://{configuration.get('S3_BUCKET_NAME')}/data/gps_data')
    query3 = streamWriter(trafficDF, f's3a://{configuration.get('S3_BUCKET_NAME')}/checkpoints/traffic_data',
                 f's3a://{configuration.get('S3_BUCKET_NAME')}/data/traffic_data')
    query4 = streamWriter(weatherDF, f's3a://{configuration.get('S3_BUCKET_NAME')}/checkpoints/weather_data',
                 f's3a://{configuration.get('S3_BUCKET_NAME')}/data/weather_data')
    query5 = streamWriter(emergencyDF, f's3a://{configuration.get('S3_BUCKET_NAME')}/checkpoints/emergency_data',
                 f's3a://{configuration.get('S3_BUCKET_NAME')}/data/emergency_data')

    query5.awaitTermination()



if __name__ == "__main__":
    main()