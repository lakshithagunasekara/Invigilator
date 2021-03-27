const request = require('request');

const frameRoutes = (app) => {

    // READ
    app.get('/results', (req, res) => {
        const student_id = req.query.id;
        if(student_id) {
            const s3_bucket_file_path = `https://invigilator-s3bucket-qljvzcoqk2zw.s3.amazonaws.com/output/${student_id}/results.json`;
            request(s3_bucket_file_path, function (error, response, body) {
                if (!error && response.statusCode == 200) {
                    try{
                        res.status(200);
                        res.send(JSON.parse(body));
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

module.exports = frameRoutes;
