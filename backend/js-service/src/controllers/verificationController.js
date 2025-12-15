const {
  aadharVerificaion,
  panVerificaion,
  dlVerification,
} = require("../services/verificationService");

async function runVerification() {
  console.log("🚀 Auto verification triggered via DB threshold...");

  const {
    getPendingEntries,
    setCustomerVerified,
    setVehicleVerificationData,
    setVerificationCompleted,
  } = require("../models/customersModel");

  const results = await getPendingEntries();
  for (const element of results) {
    let vin_result = false;
    let chassis_result = false;
    let engine_result = false;
    let verification_result = {};

    const {
      customer_id,
      name,
      aadhaar_provided,
      pan_provided,
      dl_provided,
      tax_invoice,
      dan,
      cddn,
    } = element;

    // --- CUSTOMER VERIFICATION ---
    try {
      if (aadhaar_provided) {
        const customerResult = await aadharVerificaion(element);
        if (customerResult?.status?.status_matching === "success") {
          await setCustomerVerified(true, customer_id);
          console.log(`${name}: ✅ Customer verified via Aadhaar`);
        } else {
          await setCustomerVerified(false, customer_id);
          console.log(`${name}: ❌ Aadhaar verification failed`);
        }
      } else if (pan_provided) {
        const customerResult = await panVerificaion(element);
        if (customerResult?.status?.status_matching === "success") {
          await setCustomerVerified(true, customer_id);
          console.log(`${name}: ✅ Customer verified via PAN`);
        } else {
          await setCustomerVerified(false, customer_id);
          console.log(`${name}: ❌ PAN verification failed`);
        }
      } else if (dl_provided) {
        const customerResult = await dlVerification(element);
        if (customerResult?.status?.status_matching === "success") {
          await setCustomerVerified(true, customer_id);
          console.log(`${name}: ✅ Customer verified via DL`);
        } else {
          await setCustomerVerified(false, customer_id);
          console.log(`${name}: ❌ DL verification failed`);
        }
      } else {
        console.log(`${name}: ⚠️ No verification ID provided`);
      }
    } catch (err) {
      console.error(`${name}: Error in customer verification`, err);
    }

    // --- VIN NUMBER VERIFICATION ---
    if (tax_invoice?.vin_number && dan?.vin_number && cddn?.vin_number) {
      if (
        tax_invoice.vin_number === dan.vin_number &&
        dan.vin_number === cddn.vin_number
      ) {
        vin_result = true;
        verification_result.vin =
          "All three consistent (Tax Invoice && DAN && CDDN)";
      } else if (
        tax_invoice.vin_number === dan.vin_number ||
        dan.vin_number === cddn.vin_number ||
        cddn.vin_number === tax_invoice.vin_number
      ) {
        vin_result = true;
        if (tax_invoice.vin_number === dan.vin_number)
          verification_result.vin = "Tax Invoice && DAN consistent";
        else if (dan.vin_number === cddn.vin_number)
          verification_result.vin = "DAN && CDDN consistent";
        else verification_result.vin = "Tax Invoice && CDDN consistent";
      } else {
        vin_result = false;
        verification_result.vin = "None are consistent";
      }
    } else {
      vin_result = false;
      verification_result.vin = "Incomplete data for verification";
    }

    // --- CHASSIS NUMBER VERIFICATION ---
    if (
      tax_invoice?.chassis_number &&
      dan?.chassis_number &&
      cddn?.chassis_number
    ) {
      if (
        tax_invoice.chassis_number === dan.chassis_number &&
        dan.chassis_number === cddn.chassis_number
      ) {
        chassis_result = true;
        verification_result.chassis =
          "All three consistent (Tax Invoice && DAN && CDDN)";
      } else if (
        tax_invoice.chassis_number === dan.chassis_number ||
        dan.chassis_number === cddn.chassis_number ||
        cddn.chassis_number === tax_invoice.chassis_number
      ) {
        chassis_result = true;
        if (tax_invoice.chassis_number === dan.chassis_number)
          verification_result.chassis = "Tax Invoice && DAN consistent";
        else if (dan.chassis_number === cddn.chassis_number)
          verification_result.chassis = "DAN && CDDN consistent";
        else verification_result.chassis = "Tax Invoice && CDDN consistent";
      } else {
        chassis_result = false;
        verification_result.chassis = "None are consistent";
      }
    } else {
      chassis_result = false;
      verification_result.chassis = "Incomplete data for verification";
    }

    // --- ENGINE NUMBER VERIFICATION ---
    if (
      tax_invoice?.engine_number &&
      dan?.engine_number &&
      cddn?.engine_number
    ) {
      if (
        tax_invoice.engine_number === dan.engine_number &&
        dan.engine_number === cddn.engine_number
      ) {
        engine_result = true;
        verification_result.engine =
          "All three consistent (Tax Invoice && DAN && CDDN)";
      } else if (
        tax_invoice.engine_number === dan.engine_number ||
        dan.engine_number === cddn.engine_number ||
        cddn.engine_number === tax_invoice.engine_number
      ) {
        engine_result = true;
        if (tax_invoice.engine_number === dan.engine_number)
          verification_result.engine = "Tax Invoice && DAN consistent";
        else if (dan.engine_number === cddn.engine_number)
          verification_result.engine = "DAN && CDDN consistent";
        else verification_result.engine = "Tax Invoice && CDDN consistent";
      } else {
        engine_result = false;
        verification_result.engine = "None are consistent";
      }
    } else {
      engine_result = false;
      verification_result.engine = "Incomplete data for verification";
    }

    // --- FINAL VEHICLE VERIFICATION ---
    let vehicle_verified = false;

    if (vin_result && chassis_result && engine_result) {
      vehicle_verified = true;
      verification_result.vehicle = "All three parameters are consistent";
    } else if (
      (vin_result && chassis_result) ||
      (vin_result && engine_result) ||
      (chassis_result && engine_result)
    ) {
      vehicle_verified = true;
      verification_result.vehicle = "Two parameters are consistent";
    } else if (vin_result || chassis_result || engine_result) {
      vehicle_verified = false;
      verification_result.vehicle = "Only one parameter is consistent";
    } else {
      vehicle_verified = false;
      verification_result.vehicle = "None are consistent — verification failed";
    }

    // --- Update DB ---
    try {
      await setVehicleVerificationData(
        vehicle_verified,
        verification_result,
        customer_id
      );
      console.log(`${name}: Vehicle verification updated successfully`);
    } catch (err) {
      console.error(`${name}: Failed to update vehicle verification`, err);
    }

    await setVerificationCompleted(customer_id);
  }

  console.log("✅ Verification process completed (auto-triggered)");
}

const verificationController = {
  processVerification: async (req, res) => {
    console.log("Entering manual verification route...");
    await runVerification();
    res.status(200).json({ message: "Verification process completed" });
  },
};

module.exports = { ...verificationController, runVerification };
