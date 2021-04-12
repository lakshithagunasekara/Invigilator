const AWS = require('aws-sdk');
const s3 = new AWS.S3();
const lambda = new AWS.Lambda();

const dstBucket = "invigilator-frame-input-bucket";

exports.handler = async(event, context, callback) => {

    var record = event.Records[0]; // Data not sent in batches in stream
    // Kinesis data is base64 encoded so decode here
    var kinesisData = Buffer.from(record.kinesis.data, 'base64').toString("ascii");
    var data = JSON.parse(Buffer.from(kinesisData, 'base64').toString("ascii"));

    console.log(data);
//    console.log(data['Image'])

    var userId = data['User'];
    var frameNumber = data['Frame Number'];
    // decode the again to read base64 encoded image
    var imageBuffer = new Buffer(data['Image'], 'base64');
    var finalFrame = data['Final Frame'];
    console.log(finalFrame);

    const destparams = {
        Bucket: dstBucket,
        Key: userId + "/" + frameNumber + ".jpg",
        Body: imageBuffer
    };

    try {
        const putResult = await s3.upload(destparams).promise();
        console.log("Uploading to S3 Bucket Status", putResult);
    }
    catch (err) {
        console.log("Error in uploading image to S3 Bucket", err);
    }

    console.log(finalFrame === "true");
    if (finalFrame === "true") {
      // Notify the video-processor lambda
      var params = {
        FunctionName: "image-processor-rekognition",
        InvocationType: "RequestResponse",
        LogType: "Tail",
        Payload: JSON.stringify({
          videoName: userId,
          prefix: userId + "/",
        }),
      };
      const result = await lambda.invoke(params).promise();
      console.log("Results : " + result);
    }
};
