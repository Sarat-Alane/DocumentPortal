// src/models/documentModel.js
const db = require("../config/db");

const getAllDocuments = async (limit = 200) => {
  const query = `
    SELECT 
      filename,
      customer_id,
      name,
      dob,
      gender,
      address,
      city,
      state,
      aadhaar_provided,
      aadhaar_number,
      pan_provided,
      pan_number,
      dl_provided,
      dl_number,
      rc_provided,
      vehicle_rc,
      gstin_provided,
      gstin,
      gst_company,
      verification_status,
      verification_result,
      customer_verification,
      vehicle_verification,
      -- Extract JSONB components safely
      tax_invoice->>'vin_number' AS tvin_number,
      tax_invoice->>'engine_number' AS tengine_number,
      tax_invoice->>'chassis_number' AS tchassis_number,
      dan->>'vin_number' AS dvin_number,
      dan->>'engine_number' AS dengine_number,
      dan->>'chassis_number' AS dchassis_number,
      cddn->>'vin_number' AS cvin_number,
      cddn->>'engine_number' AS cengine_number,
      cddn->>'chassis_number' AS cchassis_number
    FROM customersnew
    ORDER BY customer_id DESC
    LIMIT $1;
    `;
  const { rows } = await db.query(query, [limit]);
  return rows;
};

module.exports = { getAllDocuments };

// SELECT customer_id, name, dob, gender, address, city, state,
//        aadhaar_provided, aadhaar_number, pan_provided, pan_number,
//        dl_provided, dl_number, verification_status, verification_result,
//        vin_number, chassis_number, engine_number,
//        customer_verification, vehicle_verification,
//        vehicle_rc, rc_provided, gstin_provided, gstin, gst_company
// FROM customers
// LIMIT $1
