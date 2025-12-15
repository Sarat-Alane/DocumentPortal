const pg = require("pg");
const { runVerification } = require("../controllers/verificationController");

// Local Database
// const pool = new pg.Pool({
//   user: "postgres",
//   host: "localhost",
//   database: "carDealer",
//   password: "root", // 🔒 replace with your actual password
//   port: 5432,
//   ssl: false,
// });


// AWS Database
const pool = new pg.Pool({
    user: process.env.AWS_DB_USER,
    host: process.env.AWS_DB_HOST,
    database: process.env.AWS_DB_DATABASE,
    password: process.env.AWS_DB_PASSWORD, 
    port: Number(process.env.AWS_DB_PORT),
    ssl: { rejectUnauthorized: false },
})

async function initDbListener() {
  const client = await pool.connect();

  // Listen to row-change and threshold events
  await client.query("LISTEN customer_changes");
  await client.query("LISTEN threshold_reached");

  client.on("notification", async (msg) => {
    try {
      const payload = JSON.parse(msg.payload);
      const io = require("../app").io;

      if (msg.channel === "customer_changes") {
        // Emit live DB change to all sockets
        io.emit("dbChanged", payload);
      }

      if (msg.channel === "threshold_reached") {
        console.log("🔔 Threshold reached:", payload);

        // Emit a socket event so frontend can show “Verification started…”
        io.emit("verificationTriggered", {
          message: `Threshold reached at ${payload.count} records — starting verification process.`,
        });

        // Run the verification logic automatically
        try {
          await runVerification();
          io.emit("verificationCompleted", {
            message: "Automatic verification completed successfully.",
          });
        } catch (err) {
          console.error("❌ Auto verification failed:", err);
          io.emit("verificationFailed", {
            message: "Automatic verification failed.",
            error: err.message,
          });
        }
      }
    } catch (err) {
      console.error("⚠️ Failed to parse DB payload:", err);
    }
  });
}

initDbListener().catch((err) => console.error("DB listener failed:", err));

module.exports = pool;
