// This is the code for the actual verification service
// This is the code for the actual verification service
// This is the code for the actual verification service

const path = require("path");
const axios = require("axios");

const tokenKey = "REPLACE_API_TOKEN_KEY_HERE"; // Convert the Token Key into an environment Variable and store it in .env file

const formatDate = (dateString) => {
  const d = new Date(dateString);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const aadharVerificaion = async (element) => {
  try {
    // Define Header
    const myHeaders = new Headers();
    myHeaders.append("tokenKey", tokenKey);
    myHeaders.append("Content-Type", "application/json");

    //Process input Element parameters
    element.dob = formatDate(element.dob);

    // Define the Manual Inputs
    const manualInput = {
      id_number: element.aadhaar_number,
      name: element.name,
      dob: element.dob,
    };

    // console.log("Manual input is:", manualInput)

    // Define the Raw payload to the API
    const raw = JSON.stringify({
      docType: "ind_aadhaar",
      name_match_threshold: 100,
      success_parameters: ["id_number"],
      manual_input: manualInput,
    });

    // console.log("Raw Input is:", raw)

    // Define RequestOptions
    const requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw,
      redirect: "follow",
    };

    // Fetch API Call
    // fetch(
    //   "https://api-dev.springscan.springverify.com/v4/databaseCheck",
    //   requestOptions
    // )
    //   .then((response) => response.text())
    //   .then((result) => console.log("Result: ", result))
    //   .catch((error) => console.log("error", error));

    const response = await fetch(
      "https://api-dev.springscan.springverify.com/v4/databaseCheck",
      requestOptions
    );
    const result = await response.json();
    console.log(result)
    return result;
  } catch (error) {
    console.error("Aaadhaar Verification Error at Service Layer");
    throw error;
  } finally {
  }
};

const panVerificaion = async (element) => {
  try {
    const myHeaders = new Headers();
    // myHeaders.append("tokenKey", "REPLACE_API_TOKEN_KEY_HERE"); // Need to add Token here
    myHeaders.append("Content-Type", "application/json");
    element.dob = formatDate(element.dob);
    console.log("Element DoB:", element.dob);

    const manualInput = {
      id_number: element.pan_number,
      name: element.name,
      dob: element.dob,    // The date needs to be formatted as per PAN Card
    };

    console.log("Manual Input Provided:", manualInput);

    var raw = JSON.stringify({
      docType: "ind_pan",
      name_match_threshold: 100,

      // success_parameters: ["name"],

      manual_input: manualInput,
    });

    console.log("Raw Data is:", raw);

    var requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw,
      redirect: "follow",
    };

    // fetch(
    //   "https://api-dev.springscan.springverify.com/v4/databaseCheck",
    //   requestOptions
    // )
    //   .then((response) => response.text())
    //   .then((result) => console.log("Result: ", result))
    //   .catch((error) => console.log("error", error));

    const response = await axios.post(
      "https://api-dev.springscan.springverify.com/v4/databaseCheck",
      raw,
      {
        headers: {
          tokenKey: "REPLACE_API_TOKEN_KEY_HERE",
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Result:", response.data);
    return response.data
  } catch (error) {
    console.error("PAN Verification Error at Service Layer");
    throw error;
    // res.status(500).json({ error: "Verification failed" });
  }
};

const dlVerification = async (element) => {
  try {
    // Define headers
    const myHeaders = new Headers();
    myHeaders.append("tokenKey", tokenKey);
    myHeaders.append("Content-Type", "application/json");

    //Process input Element parameters
    element.dob = formatDate(element.dob);

    // Define Manual Input
    const manualInput = {
      id_number: element.dl_number,
      name: element.name,
      dob: element.dob,
    };

    // Define Raw payload to API
    const raw = JSON.stringify({
      docType: "ind_driving_license",
      name_match_threshold: 100,
      success_parameters: ["id_number"],
      manual_input: manualInput,
    });

    // Define the Request Options
    const requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw,
      redirect: "follow",
    };

    // Fetch API Call
    const response = await fetch(
      "https://api-dev.springscan.springverify.com/v4/databaseCheck",
      requestOptions
    );
    const result = await response.json();
    return result;
  } catch (error) {
    console.error("DL Verification Error at Service Layer");
    throw error;
  } finally {
  }
};

const rcVerification = async (element) => {
  try {
    var myHeaders = new Headers();
    myHeaders.append("tokenKey", tokenKey);
    myHeaders.append("Content-Type", "application/json");

    const manual_input = {
      rc_number: element.vehicle_rc,
      chassis_number: element.chassis_number,
      owner_name: element.name,
      // engine_number: element.engine_number,
    };

    console.log("Manual Input provided to Service: ", manual_input);

    const raw = JSON.stringify({
      docType: "ind_rc",
      success_parameters: [
        "rc_number",
        "chassis_number",
        "owner_name",
        // "engine_number",
      ],
      manual_input: manual_input,
    });

    console.log("Total Raw data: ", raw);

    const requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw,
      redirect: "follow",
    };

    const response = await fetch(
      "https://api-dev.springscan.springverify.com/v4/databaseCheck",
      requestOptions
    );
    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Vehicle Verification Error at Service Layer");
    throw error;
  } finally {
  }
};

const gstVerification = async (element) => {
  try {
    var myHeaders = new Headers();
    myHeaders.append("tokenKey", tokenKey);
    myHeaders.append("Content-Type", "application/json");

    var raw = JSON.stringify({
      docType: "ind_gst_certificate",
      manual_input: {
        gstin: element.gstin,
      },
    });

    var requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw,
      redirect: "follow",
    };

    const response = await fetch(
      "https://api-dev.springscan.springverify.com/v4/databaseCheck",
      requestOptions
    );
    const request = await response.json();
    return request;
  } catch (error) {
    console.error("GSTIN Verification Error at Service Layer");
    throw error;
  } finally {
  }
};

module.exports = {
  aadharVerificaion,
  panVerificaion,
  dlVerification,
  rcVerification,
  gstVerification,
};
