// This is a mock verification service
// This is a mock verification service
// This is a mock verification service


const path = require("path")
const axios = require("axios")

const mock_aadhaar_db = {
    "123456789012" : {"name": "Rahul Sharma", "dob": "2000-01-01", "gender": "Male", "city": "Delhi", "state": "Delhi"},
    "987654321098": {"name": "Priya Verma", "dob": "2000-02-02", "gender": "Female", "city": "Panaji", "state": "Goa"},
    "820723357808": {"name": "Gyanendra Kumar Shukla", "dob": "1952-08-15", "gender": "Male", "city": "Kanpur", "state": "Uttar Pradesh"},
    "954665782924": {"name": "Supriya Shukla", "dob": "1955-03-19", "gender": "Female", "city": "Kanpur", "state": "Uttar Pradesh"},
}

const mock_pan_db = {
    "ABOPS2678H" : {"name": "Gyanendra Kumar Shukla", "dob": "1952-08-15", "gender": "Male", "city": "Kanpur", "state": "Uttar Pradesh"},
    "ABCDE1234F": {"name": "Rahul Sharma", "dob": "1990-05-15", "gender": "Male", "address": "Mumbai, Maharashtra", "city": "Mumbai", "state": "Maharashtra"},
    "PQRSX5678Y": {"name": "Priya Verma", "dob": "1995-10-02", "gender": "Female", "address": "Delhi, India", "city": "Delhi"},
}

const mock_dl_db = {
    "MH1420110012345": {"name": "Rahul Sharma", "dob": "1990-05-15", "gender": "Male", "address": "Mumbai, Maharashtra", "city": "Mumbai", "state": "Maharashtra"},
    "DL0920150056789": {"name": "Priya Verma", "dob": "1995-10-02", "gender": "Female", "address": "Delhi, India", "city": "Delhi"},
}

const getDataByAadhaar = async (aadhaar_number) => {
    return mock_aadhaar_db[aadhaar_number];
}

const getDataByPan = async (pan_number) => {
    return mock_pan_db[pan_number];
}

const getDataByDL = async (dl_number) => {
    return mock_dl_db[dl_number];
}

module.exports = { getDataByAadhaar, getDataByPan, getDataByDL }