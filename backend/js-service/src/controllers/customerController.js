const axios = require("axios");
const FormData = require("form-data");
const { Readable } = require("stream");
const { PutObjectCommand } = require("@aws-sdk/client-s3");
const { s3Client, BUCKET_NAME } = require("../config/s3config");
const fs = require("fs");
const { getPendingEntries } = require("../models/customersModel");

const pendingJobs = {};

const customerController = {
  // Step 1: Handle PDF upload
  addPdf: async (req, res) => {
    try {
      const file = req.file;
      if (!file) return res.status(400).json({ error: "No file uploaded" });

      const jobId = Date.now().toString(); // unique ID
      const key = `incoming/${jobId}-${file.originalname}`;

      await s3Client.send(
        new PutObjectCommand({
          Bucket: BUCKET_NAME,
          Key: key,
          Body: file.buffer,
          ContentType: file.mimetype,
        })
      );

      console.log("✅ Uploaded to S3:", key);

      // respond immediately so frontend doesn't hang
      return res.status(202).json({
        message: "Upload accepted",
        jobId,
        key,
      });
    } catch (err) {
      console.error("❌ S3 Upload / Processing Error:", err);
      return res.status(500).json({ error: "Failed to process PDF" });
    }
  },

  // Step 2: Handle worker notification
  notifyPdfProcessed: async (req, res) => {
    try {
      const { jobId, processedData } = req.body;

      if (!jobId) return res.status(400).json({ error: "Missing jobId" });

      const response = pendingJobs[jobId];
      if (!response) return res.status(404).json({ error: "Job not found" });

      let customerEntries = await getPendingEntries();
      // Render dashboard with processed data
      res.render("dashboard", { customerEntries });

      // Cleanup
      delete pendingJobs[jobId];

      // Respond to worker
      res.status(200).json({ success: true });
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: "Failed to handle worker notification" });
    }
  },

  getPendingRows: async (req, res) => {
    let customerEntries = await getPendingEntries();
    // Render dashboard with processed data
    res.render("dashboard", { customerEntries });
  },
};

module.exports = customerController;
