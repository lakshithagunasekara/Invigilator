import logo from './logo.svg';
import './App.css';
import VideoRecorder from 'react-video-recorder';
import S3 from "react-aws-s3";
import * as AWS from "aws-sdk";


function App() {

    // const SESConfig = {
    //     apiVersion: "2010-12-01",
    //     accessKeyId: "AKIAXJTZRA37HBWZUM4U",
    //     accessSecretKey: "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",
    //     region: "us-east-1"
    // }
    // // AWS.config.update(SESConfig);
    //
    // AWS.config.update(SESConfig);
    // AWS.config.update({
    //     credentials: new AWS.CognitoIdentityCredentials({
    //         IdentityPoolId: 'us-east-1:f1899ed5-00c6-4808-943a-ba0ef645a8f7',
    //     }),
    //     region: 'us-west-2'
    // });

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
    // REACT_APP_ACCESS_ID=AKIAXJTZRA37HBWZUM4U
    // REACT_APP_ACCESS_KEY=RdMu2JiT0mHvJTKzKg7Zmp4rP9RTi2r2RfTpjnWnXXXXXX
    // REACT_APP_BUCKET_NAME=invtest2
    // REACT_APP_DIR_NAME=mydir
    // REACT_APP_REGION=us-east-1
    // const config = {
    //     bucketName: "invtest2",
    //     region: "us-east-1",
    //     accessKeyId: "AKIAXJTZRA37HBWZUM4U",
    //     secretAccessKey: "RdMu2JiT0mHvJTKzKg7Zmp4rP9RTi2r2RfTpjnWnXXXXXX"
    // };


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

                        // const ReactS3Client = new S3(config);
                        // ReactS3Client.uploadFile(videoBlob, 'video.mp4').then(
                        //     data =>{
                        //         console.log(data);
                        //     }
                        //
                        // )

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
