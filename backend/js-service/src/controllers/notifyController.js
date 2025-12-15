const db = require("../config/db");

const notifyController = {
  pdfProcessed: async (req, res) => {
    const io = req.app.locals.io;
    const { jobId, processedData } = req.body;

    try {
      // Option A: If worker already wrote to DB, you can simply fetch the new row by jobId and emit it.
      // Option B: If worker did NOT write to DB, insert processedData here.
      // We'll show example of fetching by some unique field (assume customer_id present)
      // For safety, try to fetch the just-inserted row from DB using an identifier in processedData

      // Example: processedData contains customer_id
      const customerId = processedData.customer_id;
      let newRow = null;

      if (customerId) {
        const { rows } = await db.query(
          `SELECT * FROM customer_entries WHERE customer_id = $1 LIMIT 1`,
          [customerId]
        );
        newRow = rows[0] || null;
      }

      // If newRow is null, optionally create a minimal payload from processedData
      const payload = newRow || processedData;

      // Emit socket event to all clients (or you can emit to specific rooms)
      io.emit("documentProcessed", { jobId, payload });

      res.status(200).json({ message: "Notified clients", jobId });
    } catch (err) {
      console.error("Error in /pdfProcessed:", err);
      res.status(500).json({ error: "Server error" });
    }
  },
};

module.exports = notifyController;
