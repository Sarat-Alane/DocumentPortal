const express = require("express");
const path = require("path");
const fs = require("fs");
const multer = require("multer");

const customerController = require("../controllers/customerController");
const verificationController = require("../controllers/verificationController");
const notifyController = require("../controllers/notifyController");
const documentController = require("../controllers/documentController");
const redirectionController = require("../controllers/redirectionController");

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

const router = express.Router();

router.get("/", redirectionController.index);

router.get("/verify", verificationController.processVerification);    // This is a temporary route for direct verification. Remove this route after testing

router.post(
  "/uploadPDF",
  upload.single("pdf"), // <--- attach multer
  customerController.addPdf
);

router.post("/pdfProcessed", notifyController.pdfProcessed);

router.get("/getPendingEntries", customerController.getPendingRows);

router.post("/pdfProcessed", customerController.notifyPdfProcessed);

router.get("/documents", documentController.getDocuments);

// router.get("/verifyCustomer/:id", customerController.someFunction);

router.get("/processVerification", verificationController.processVerification);

module.exports = router;
