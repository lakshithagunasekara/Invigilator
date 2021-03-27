const AWS = require('aws-sdk');
const axios = require('axios');
const s3 = new AWS.S3();

exports.handler = async(event, context, callback) => {

    var record = event.Records[0].s3;
    var url = "https://" + record.bucket.name + ".s3.amazonaws.com/" + record.object.key;

    var data = JSON.stringify({
    "url":url,
    "stream":"frame-input-stream",
    "rate": "1000",
    "partition":"0"}
    );
    console.log(data);

    var config = {
      method: 'post',
      url: 'http://ec2-54-87-208-253.compute-1.amazonaws.com:8080/process',
      headers: {
        'Content-Type': 'application/json'
      },
      data : data
    };
    console.log(config);

    await axios(config)
    .then(function (response) {
      console.log("success");
      console.log(JSON.stringify(response.data));
    })
    .catch(function (error) {
      console.log("error");
      console.log(error);
    });
    return;
};