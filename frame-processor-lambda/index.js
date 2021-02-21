const AWS = require('aws-sdk');
const s3 = new AWS.S3();

const dstBucket = "frame-input-bucket";

exports.handler = async(event, context, callback) => {

    var record = event.Records[0]; // Data not sent in batches in stream
    // Kinesis data is base64 encoded so decode here
    var kinesisData = Buffer.from(record.kinesis.data, 'base64').toString("ascii");
    var data = JSON.parse(Buffer.from(kinesisData, 'base64').toString("ascii"));

    console.log(data);
    console.log(data['Image'])

    var userId = data['User'];
    var timestamp = data['Timestamp'];
    // decode the again to read base64 encoded image
    var imageBuffer = new Buffer(data['Image'], 'base64');

    const destparams = {
        Bucket: dstBucket,
        Key: userId + "-" + timestamp + ".jpg",
        Body: imageBuffer
    };

    try {
        const putResult = await s3.upload(destparams).promise();
        console.log("Upolading to S3 Bucket Status", putResult);
    }
    catch (err) {
        console.log("Error in uploading image to S3 Bucket", err);
    }
};

