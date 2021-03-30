const request = require('request');
const fs = require('fs');
const carbone = require('carbone');
const _  = require('lodash');

const bucket = 'https://invigilator-s3bucket-qljvzcoqk2zw.s3.amazonaws.com/';

const frameRoutes = (app) => {

    // READ
    app.get('/results', (req, res) => {
        const student_id = req.query.id;
        if(student_id) {
            const s3_bucket_file_path = `${bucket}output/${student_id}/results.json`;
            request(s3_bucket_file_path, function (error, response, body) {
                if (!error && response.statusCode == 200) {
                    try{
                        console.log("success")
                        res.status(200);
                        res.send(JSON.parse(body));
                        // const data = JSON.parse(body);
                        // generateDoc(data)
                        // res.download('./results.docx',  'results.docx', function(err){
                        //     if (err) {
                        //         throw err;
                        //     }
                        // });
                    } catch (e) {
                        res.status(500);
                        console.log("json parse error ", e);
                        res.send(e);
                    }
                } else {
                    console.log("request error " , response.body)
                    res.status(400);
                    res.send(response.body);
                }
            });
        } else {
            res.status(422);
            res.send("empty student id");
        }

    });
};


const formatData = function (data) {
    let new_obj = _.cloneDeep(data);
    const timestamp_id_arr = _.get(data, 'user_id').split('_');
    _.set(new_obj, 'user_id', timestamp_id_arr[1]);
    _.set(new_obj, 'date', new Date(+timestamp_id_arr[0]).toLocaleDateString());
    _.set(new_obj, 'start_time', new Date(+timestamp_id_arr[0]).toLocaleTimeString());
    _.set(new_obj, 'empty_frames_found', new_obj['empty frames_found']);

    _.map(new_obj.faces, f => {
        f.face_url = `${bucket}${f.face_url}`;
        // _.map(f.frame_ids, id => `${bucket}${new_obj.frame_prefix}${id}`)
        return f;
    } )

    return new_obj;
}


const generateDoc = function (data){
    data= formatData(data);
    carbone.render('./template.docx', data, function(err, result){
        if (err) {
            throw err;
        }
        fs.writeFileSync('results.docx', result);
    });
}

module.exports = frameRoutes;
