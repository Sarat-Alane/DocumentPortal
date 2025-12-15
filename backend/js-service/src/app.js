const express = require("express");
const http = require("http");
const path = require("path");
const fs = require("fs");
const bodyParser = require("body-parser");
const multer = require("multer");
// const ejs = require("ejs");
const { Server } = require("socket.io");
const cors = require("cors");
require("dotenv").config({ path: require("path").join(__dirname, "..", ".env") });

const app = express();
const PORT = 3000;

// ✅ Allow cross-origin requests from React dev server (Vite usually runs at 5173)
app.use(cors({
  origin: "http://localhost:5173",
  methods: ["GET", "POST"],
  credentials: true,
}));

app.use(express.json()); // ✅ Parse JSON bodies
app.use(express.urlencoded({ extended: true })); // for form data
console.log(path.join(__dirname, "..", "..", "..", "frontend"))
app.use(express.static(path.join(__dirname, "..", "..", "..", "frontend", "dist")));
// app.use(express.static(path.join(__dirname, "..", "..", "..","my-app")));

// app.set("view engine", "ejs");
// app.set("views", path.join(__dirname, "views"));

const routes = require("./routes");
app.use("/", routes);

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*", // restrict in production
    methods: ["GET", "POST"]
  }
});

// make io accessible to routes/controllers via app.locals
app.locals.io = io;

io.on("connection", (socket) => {
  console.log("Socket connected:", socket.id);

  socket.on("disconnect", () => {
    console.log("Socket disconnected:", socket.id);
  });
});


server.listen(PORT, "0.0.0.0", () => console.log(`Server running at http://localhost:${PORT}`));


module.exports = { app, io };