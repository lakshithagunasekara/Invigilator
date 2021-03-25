import logo from './logo.svg';
import './App.css';
import VideoRecorder from 'react-video-recorder';
import * as AWS from "aws-sdk";


function App() {

// Initialize the Amazon Cognito credentials provider
    AWS.config.region = 'us-east-1'; // Region
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
        IdentityPoolId: 'us-east-1:f1899ed5-00c6-4808-943a-ba0ef645a8f7',
    });

    const s3 = new AWS.S3({
        params: {
            Bucket: 'shanwije-inv-0419'
        }
    });


    return (
        <div className="App">
            <header className="App-header">
                <img src={logo} className="App-logo" alt="logo"/>
                <p>
                    Edit <code>src/App.js</code> and save to reload.
                </p>
                <VideoRecorder
                    onRecordingComplete={videoBlob => {
                        // Do something with the video...
                        console.log('videoBlob', videoBlob)

                        s3.putObject({
                                Key: "video.mp4",
                                Body: videoBlob,
                                'ContentType': 'video/mp4',
                                ACL: 'public-read'
                            }, (err) => {
                                if (err) {
                                    // On Error
                                    console.log(err)
                                } else {
                                    console.log("success")
                                    // On Success
                                }
                            }
                        )
                    }}
                />
            </header>
        </div>
    );
}

export default App;
