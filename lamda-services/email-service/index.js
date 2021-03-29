
// Load the AWS SDK for Node.js
var aws = require('aws-sdk');

// Create a new SES object in ap-south-1 region
var ses = new aws.SES({region: 'ap-south-1'});

exports.handler = (event, context, callback) => {
    
     var params = {
        Destination: {
            ToAddresses: ["reciever@gmail.com"]
        },
        Message: {
            Body: {
                Text: { Data: "Hi there, this message is sent from invigilator."
                    
                }
                
            },
            
            Subject: { Data: "Invigilator"
                
            }
        },
        Source: "sender@outlook.com"
    };

    
     ses.sendEmail(params, function (err, data) {
        callback(null, {err: err, data: data});
        if (err) {
            console.log("Error")
            console.log(err);
            context.fail(err);
        } else {
            console.log("succeed")
            console.log(data);
            context.succeed(event);
        }
    });
};