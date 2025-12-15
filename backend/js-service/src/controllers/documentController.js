const { getAllDocuments } = require("../models/documentModel");

const documentController = {
  getDocuments: async (req, res) => {
    try {
      const documents = await getAllDocuments(200);
      res.status(200).json(documents);
    } catch (err) {
      console.error("getDocuments error:", err);
      res.status(500).json({ error: "Failed to fetch documents" });
    }
  },
};

module.exports = documentController;