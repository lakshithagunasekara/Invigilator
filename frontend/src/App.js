import logo from './logo.svg';
import './App.css';
import VideoRecorder from 'react-video-recorder';
import * as AWS from "aws-sdk";
import { v4 as uuidv4 } from 'uuid';


function App() {

    // Initialize the Amazon Cognito credentials provider
    AWS.config.region = 'us-east-1'; // Region
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
        IdentityPoolId: 'us-east-1:ead1028d-6385-4279-affc-4612957bdf2c',
    });

    const userId = new Date().valueOf() + "_" + uuidv4();

    const videoFileName = `input/${userId}.mp4`;
    const s3BasePath = `https://invigilator-s3bucket-qljvzcoqk2zw.s3.amazonaws.com/${videoFileName}`;

    const s3 = new AWS.S3({
        params: {
            Bucket: 'invigilator-s3bucket-qljvzcoqk2zw'
        }
    });

    return (
        <div className="App">
                <VideoRecorder
                    onRecordingComplete={videoBlob => {
                        // Do something with the video...
                        console.log('videoBlob', videoBlob)

                        s3.putObject({
                                Key: videoFileName,
                                Body: videoBlob,
                                'ContentType': 'video/mp4',
                                ACL: 'public-read'
                            }, (err) => {
                                if (err) {
                                    // On Error
                                    console.log(err)
                                } else {
                                    console.log("success")
                                    console.log(s3BasePath)
                                    // On Success
                                }
                            }
                        )
                    }}
                />
        </div>
    );
}

export default App;
