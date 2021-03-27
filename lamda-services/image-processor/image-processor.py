import boto3
import json
import os
import sys
import time
import random
import math
from datetime import datetime
from Queue import Queue
from threading import Thread
from PIL import Image, ImageDraw
from StringIO import StringIO


CONCURRENT_THREADS = 50
s3Bucket = 'invigilator-s3bucket-qljvzcoqk2zw'

def lambda_handler(event, context):
    userId = event['Event']['videoName']
    prefix = event['Event']['prefix']

    rekognition = boto3.client('rekognition', region_name=os.environ['AWS_REGION'])
    s3 = boto3.client('s3', region_name=os.environ['AWS_REGION'])

    faces = {}
    faceIDs = []
    emptyFrames = []
    facesOutput = []


    # Create a new collection in Amazon Rekognition. The user id is
    # used as the name of the collection.
    try:
        collectionId = userId
        try:
            rekognition.delete_collection(CollectionId=collectionId)
        except:
            pass
        rekognition.create_collection(CollectionId=collectionId)
        print('Collection {} created in Amazon Rekognition'.format(collectionId))

    except Exception as e:
        print('Failed to create the collection in Amazon Rekognition')
        print(e)
        raise(e)


    # Retrieve the list of thumbnail objects in the S3 bucket that were created
    # The list of keys is stored in the local variable 'thumbnailKeys'.
    try:
        thumbnailKeys = []
        paginator = s3.get_paginator('list_objects')
        response_iterator = paginator.paginate(
            Bucket=s3Bucket,
            Prefix=prefix
        )

        for page in response_iterator:
            thumbnailKeys += [i['Key'] for i in page['Contents']]

        print('Number of thumbnail objects found in the S3 bucket: {}'.format(len(thumbnailKeys)))

    except Exception as e:
        print('Failed to list the thumbnail objects')
        print(e)
        raise(e)
        
        
    # Call the IndexFaces operation for each thumbnail. 50 concurrent
    # threads are used. Each iteration of a thread lasts at least one second. Faces
    # detected are stored in a local variable 'faces'.
    indexFacesQueue = Queue()

    def index_faces_worker():
        rekognition = boto3.client('rekognition', region_name=os.environ['AWS_REGION'])

        while True:
            key = indexFacesQueue.get()
            try:
                startTime = datetime.now()
                frameNumber = int(key[:-4][-5:])
                response = rekognition.index_faces(
                    CollectionId=collectionId,
                    Image={'S3Object': {
                        'Bucket': s3Bucket,
                        'Name': key
                    }},
                    ExternalImageId=str(frameNumber)
                )
                
                for face in response['FaceRecords']:
                    faceId = face['Face']['FaceId']
                    faceIDs.append(faceId)
                    faces[faceId] = {
                        'frame_number': frameNumber,
                        'bounding_box': face['Face']['BoundingBox']
                    }
                if (len(response['FaceRecords'])) == 0:
                    emptyFrames.append(frameNumber)
                
                endTime = datetime.now()
                delta = int((endTime - startTime).total_seconds() * 1000)
                if delta < 1000:
                    timeToWait = float(1000 - delta)/1000
                    time.sleep(timeToWait)

            # The key is put back in the queue if the IndexFaces operation
            except:
                indexFacesQueue.put(key)

            indexFacesQueue.task_done()

    for i in range(CONCURRENT_THREADS):
        t = Thread(target=index_faces_worker)
        t.daemon = True
        t.start()

    for key in thumbnailKeys:
        indexFacesQueue.put(key)

    indexFacesQueue.join()
    time.sleep(2)
    

    # Search for faces that are similar to each face detected by the IndexFaces
    # operation with a confidence in matches that is higher than 97%.

    for faceId in faceIDs:
        try:
            response = rekognition.search_faces(
                CollectionId=collectionId,
                FaceId=faceId,
                FaceMatchThreshold=90,
                MaxFaces=4096
            )
            matchingFaces = [i['Face']['FaceId'] for i in response['FaceMatches']]

            # Delete the face from the local variable 'faces' if it has no
            # matching faces
            baseFramNumber = faces[faceId]['frame_number']
            framesWithFace = [faces[faceId]['frame_number']]
            if len(matchingFaces) > 0:
                faces[faceId]['matching_faces'] = matchingFaces
                for matchingFace in matchingFaces:
                    faceIDs.remove(matchingFace)
                    framesWithFace.append(faces[matchingFace]['frame_number'])
                    
            faceOutput = {
                'face_id': faceId,
                'frames': framesWithFace,
                'bounding_box' : faces[faceId]['bounding_box'],
                'base_frame' : baseFramNumber,
                'face_url' : ''
            }
            facesOutput.append(faceOutput)
        except:
            print('Failed to search for face in' + faceId)
            print(e)
            raise(e)
    
    # Create a visual representation
    for face in facesOutput:
        key = prefix + getZeros(face['base_frame']) + str(face['base_frame'])
        key += '.png'
        response = s3.get_object(Bucket=s3Bucket, Key=key)
        imgThumb = Image.open(StringIO(response['Body'].read()))

        
        # Calculate the face position to crop the image
        boxLeft = int(math.floor(imgThumb.size[0] * face['bounding_box']['Left']))
        boxTop = int(math.floor(imgThumb.size[1] * face['bounding_box']['Top']))
        boxWidth = int(math.floor(imgThumb.size[0] * face['bounding_box']['Width']))
        boxHeight = int(math.floor(imgThumb.size[1] * face['bounding_box']['Height']))


        # Paste the face thumbnail into the visual representation
        imgThumbCrop = imgThumb.crop((boxLeft, boxTop, boxLeft+boxWidth, boxTop+boxHeight))
        img = Image.new('RGB', (boxWidth, boxHeight), 'white')
        draw = ImageDraw.Draw(img)
        img.paste(imgThumbCrop)
        img.save('/tmp/img.png', 'PNG')

        try:
            key = prefix.replace('elastictranscoder/', 'output/')[:-1] + face['face_id'] + '.png'
            s3.upload_file(
                '/tmp/img.png',
                Bucket=s3Bucket,
                Key=key
            )
            print('Visual representation uploaded into the S3 bucket')
            face['face_url'] = key
            del face['bounding_box']
            del face['base_frame']
        except Exception as e:
            print('Failed to upload the visual representation into the S3 bucket')
            print(e)
            raise(e)
        
    output_json = {
        'user_id' :  userId,
        'multiple_faces_found': True if len(facesOutput) > 1 else False,
        'frame_prefix' : prefix,
        'faces' : facesOutput,
        'empty_frames_found' : True if len(emptyFrames) > 1 else False,
        'empty_frames' : emptyFrames
    }   
    print('Output',output_json)
    
    # Upload the JSON result into the S3 bucket
    try:
        s3.put_object(
            Body=json.dumps(output_json, indent=4).encode(),
            Bucket=s3Bucket,
            Key=prefix.replace('elastictranscoder/', 'output/')[:-1] + 'result.json'
        )
        print('JSON result uploaded into the S3 bucket')

    except Exception as e:
        print('Failed to upload the JSON result into the S3 bucket')
        print(e)
        raise(e)
            
            
def getZeros(number):
    if number <10:
         return '0000'
    elif number < 100:
        return '000'
    elif number < 1000:
        return '00'
    elif number < 10000:
        return '0'
    else:
        return ''