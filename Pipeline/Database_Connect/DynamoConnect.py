import os
import boto3
import subprocess
import random
import uuid
import urllib.request
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from shutil import copyfile

# predefined values for region and endpoint
dynamodb_region = 'us-west-2'
dynamodb_endpoint ='http://dynamodb.us-west-2.amazonaws.com'

def upload_image(image_path, source_name):
    """
    Uploads the given image to the s3 bucket with a random identifier.
    Creates a new item in the database with the identifier.
    """

    # generate a random unique string, highly unlikely that two of these will clash
    unique_id = str(uuid.uuid4())

    # make a copy of the image to a new file with the unique file path
    copy_image = unique_id + '.jpg'
    copyfile(image_path, copy_image)

    # send new unique file to s3 and delete it from local storage
    new_link = post_image(copy_image)
    os.remove(copy_image)

    # add the unique id to the database
    post_database(unique_id, source_name)

    return new_link

def post_image(image_path):
    """
    Posts the given image to the amazon s3 lsst-images bucket.
    Returns the link to the image on s3.
    """

    # our bucket name
    bucket_name = 'lsst-images'

    # get amazon storage
    s3 = boto3.resource('s3')

    # upload image to s3 and make it public readable
    s3.Bucket(bucket_name).upload_file(image_path, image_path, ExtraArgs={'ACL':'public-read'})

    # get the zone for the bucket, to be added to the url
    bucket_zone = boto3.client('s3').get_bucket_location(Bucket=bucket_name)

    # get the link for the image, this will be sent to the database
    image_link = "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        bucket_zone['LocationConstraint'],
        bucket_name,
        image_path
    )

    return image_link

def post_database(image_id, source_name):
    """
    Creates a new item in the database with the given image id.
    """

    # access the dynamodb
    dynamodb = boto3.resource('dynamodb', region_name=dynamodb_region, endpoint_url=dynamodb_endpoint)

    images_table = dynamodb.Table('Images')

    put_response = images_table.put_item(
        Item={
            'ID': image_id,
            'Source': source_name,
            'Label': 'NULL'
        }
    )

    return put_response

def random_image():
    """
    Retrieves a random image url by getting a random item from the database and creating its url string.
    """

    # access the dynamodb
    dynamodb = boto3.resource('dynamodb', region_name=dynamodb_region, endpoint_url=dynamodb_endpoint)
    table = dynamodb.Table('Labels')

    # take arandom value from all the values currently in the table
    response = table.scan()
    randomIndex = random.randint(0,response['Count'] - 1)

    items = response['Items']

    random_image_id = items[randomIndex]['Image-ID']

    link = get_image_link(random_image_id)

    return link

def get_image_link(image_id):
    """
    Generates a url string for a given image id.
    Used for creating random url link to image.
    """

    # our bucket name
    bucket_name = 'lsst-images'

    # get the zone for the bucket, to be added to the url
    bucket_zone = boto3.client('s3').get_bucket_location(Bucket=bucket_name)

    image_link = "https://s3-{0}.amazonaws.com/{1}/{2}.png".format(
        bucket_zone['LocationConstraint'],
        bucket_name,
        image_id
    )

    return image_link

def delete_image(image_id):
    """
    deletes all data in the database and s3 associated with this id
    """

    # access the dynamodb
    dynamodb = boto3.resource('dynamodb', region_name=dynamodb_region, endpoint_url=dynamodb_endpoint)

    images_table = dynamodb.Table('Images')

    try:
        images_delete_response = images_table.delete_item(
            Key={
                "ID": image_id
            }
        )
    except ClientError as exception:
        print(exception.response['Error']['Message'])

    return images_delete_response

def get_image_info(image_id):
    """
    retrieves the data for the given image
    """

     # access the dynamodb
    dynamodb = boto3.resource('dynamodb', region_name=dynamodb_region, endpoint_url=dynamodb_endpoint)

    images_table = dynamodb.Table('Images')

    try:
        matches = images_table.get_item(
            Key={
                "ID": image_id
            }
        )
    except ClientError as exception:
        print(exception.response['Error']['Message'])

    image_data = matches['Item']

    return image_data