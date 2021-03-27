
const frameRoutes = (app, fs) => {

    // variables
    const s3_bucket_file_path = './data/results.json';

    // READ
    app.get('/results', (req, res) => {
        fs.readFile(s3_bucket_file_path, 'utf8', (err, data) => {
            if (err) {
                throw err;
            }

            res.send(JSON.parse(data));
        });
    });
};

module.exports = frameRoutes;
