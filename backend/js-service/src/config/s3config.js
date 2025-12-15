const { S3Client } = require("@aws-sdk/client-s3");

// ⚠️ Temporary hard-coded credentials (testing only)
const s3Client = new S3Client({
  region: "eu-north-1", // your AWS region
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  },
});

const BUCKET_NAME = "addocverifybucket1"; // ✅ actual bucket name (not ARN or URL)

// export const BUCKET_NAME = "addocverifybucket1";

module.exports = {s3Client, BUCKET_NAME}