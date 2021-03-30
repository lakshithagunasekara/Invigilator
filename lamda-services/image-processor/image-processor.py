import boto3
import json
import os
import sys
import time
import random
import math
from PIL import Image, ImageDraw
from StringIO import StringIO


CONCURRENT_THREADS = 50
inputBucket = 'invigilator-frame-input-bucket'
outputBucket = 'invigilator-output-bucket'
awsRegion = 'us-east-1'

def lambda_handler(event, context):
    userId = event['Event']['videoName']
    prefix = event['Event']['prefix']
    
    print(json.dumps(event))

    rekognition = boto3.client('rekognition', region_name=awsRegion)
    s3 = boto3.client('s3', region_name=awsRegion)

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
            Bucket=inputBucket,
            Prefix=prefix
        )

        for page in response_iterator:
            thumbnailKeys += [i['Key'] for i in page['Contents']]
            print(page)

        print('Number of thumbnail objects found in the S3 bucket: {}'.format(len(thumbnailKeys)))

    except Exception as e:
        print('Failed to list the thumbnail objects')
        print(e)
        raise(e)
        
        
    # Call the IndexFaces operation for each thumbnail. 50 concurrent
    # threads are used. Each iteration of a thread lasts at least one second. Faces
    # detected are stored in a local variable 'faces'.
    
    
    for key in thumbnailKeys:
        frameNumber = int(key.replace(userId+"/", '')[:-4])
    
        try:
            response = rekognition.index_faces(
                CollectionId=collectionId,
                Image={'S3Object': {
                    'Bucket': inputBucket,
                    'Name': key
                }},
                ExternalImageId=str(frameNumber)
            )
            print(json.dumps(response))
                
            for face in response['FaceRecords']:
                faceId = face['Face']['FaceId']
                faceIDs.append(faceId)
                faces[faceId] = {
                    'frame_number': frameNumber,
                    'bounding_box': face['Face']['BoundingBox']
                }
            if (len(response['FaceRecords'])) == 0:
                emptyFrames.append(frameNumber)
        except Exception as e:
            print("Exception ", e)
        

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
        key = prefix + str(face['base_frame'])
        key += '.png'
        response = s3.get_object(Bucket=inputBucket, Key=key)
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
            key = userId + "/" + face['face_id'] + '.png'
            s3.upload_file(
                '/tmp/img.png',
                Bucket=outputBucket,
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
        key = userId + "/" + 'result.json'
        s3.put_object(
            Body=json.dumps(output_json, indent=4).encode(),
            Bucket=outputBucket,
            Key=key
        )
        print('JSON result uploaded into the S3 bucket')

    except Exception as e:
        print('Failed to upload the JSON result into the S3 bucket')
        print(e)
        raise(e)
    client = boto3.client("lambda")
    inputParams = {
        "UserID" : userId
    }
    
    response = client.invoke(
        FunctionName = 'arn:aws:lambda:us-east-1:306694957374:function:email-lambda-service',
        InvocationType = 'RequestResponse',
        Payload = json.dumps(inputParams)
    )
        
    return output_json
            
    