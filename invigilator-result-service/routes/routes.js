// import other routes
const userRoutes = require('./results');

const appRouter = (app, fs) => {

    // default route
    app.get('/', (req, res) => {
        res.send(404);
    });

    // // other routes
    userRoutes(app, fs);

};

module.exports = appRouter;