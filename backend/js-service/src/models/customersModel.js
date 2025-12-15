// const pool = require("../config/db");

// const getPendingEntries = async () => {
//   const results = await pool.query(
//     "SELECT * FROM customersnew where customer_id = 336;"
//   );
//   return results.rows;
// };

// const setCustomerVerified = async (result, tupleID) => {
//   pool.query(
//     `update customersnew set customer_verification = $1 where customer_id = $2`,
//     [result, tupleID]
//   );
// };

// const setVehcileVerified = async (result, tupleID) => {
//   pool.query(
//     `update customersnew set vehicle_verification = $1 where customer_id = $2`,
//     [result, tupleID]
//   );
// };

// module.exports = { getPendingEntries, setCustomerVerified, setVehcileVerified };




const pool = require("../config/db");

// Fetch entries pending for verification
const getPendingEntries = async () => {
  const results = await pool.query(
    "SELECT * FROM customersnew WHERE verification_status='pending';"
  );
  return results.rows;
};

// Update customer verification status (true/false)
const setCustomerVerified = async (result, tupleID) => {
  await pool.query(
    `UPDATE customersnew 
     SET customer_verification = $1 
     WHERE customer_id = $2`,
    [result, tupleID]
  );
};

// Update vehicle verification status (true/false)
const setVehicleVerified = async (result, tupleID) => {
  await pool.query(
    `UPDATE customersnew 
     SET vehicle_verification = $1 
     WHERE customer_id = $2`,
    [result, tupleID]
  );
};

// Update verification_result JSONB field
const setVerificationResult = async (resultJSON, tupleID) => {
  await pool.query(
    `UPDATE customersnew 
     SET verification_result = $1 
     WHERE customer_id = $2`,
    [resultJSON, tupleID]
  );
};

// Combined update (optional utility)
const setVehicleVerificationData = async (result, resultJSON, tupleID) => {
  await pool.query(
    `UPDATE customersnew 
     SET vehicle_verification = $1, verification_result = $2 
     WHERE customer_id = $3`,
    [result, resultJSON, tupleID]
  );
};

const setVerificationCompleted = async (tupleID) => {
  await pool.query(
    `UPDATE customersnew 
     SET verification_status = 'completed'
     WHERE customer_id = $1`,
    [tupleID]
  );
};


module.exports = {
  getPendingEntries,
  setCustomerVerified,
  setVehicleVerified,
  setVerificationResult,
  setVehicleVerificationData,
  setVerificationCompleted,
};
