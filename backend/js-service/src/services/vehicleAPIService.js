// This is Mock Verifictaion Service
// This is Mock Verifictaion Service
// This is Mock Verifictaion Service


const mock_vehicle_db = {
    "MEXBPAPB3SG011917": {"owner_name": "Gyanendra Kumar Shukla", "chassis_number": "MEXBPAPB3SG011917", "engine_number": "DZW038172", "registration_date": "2015-06-10", "city": "Kanpur", "state": "Uttar Pradesh"},
    "TMBBUJNA5EG017614": {"owner_name": "Supriya Shukla", "chassis_number": "TMBBUJNA5EG017614", "engine_number": "4G63T9A34567", "registration_date": "2020-11-05", "city": "Kanpur", "state": "Uttar Pradesh"},
    "1HGCM82633A004352": {"owner_name": "Rahul Sharma", "chassis_number": "1HGCM82633A004352", "engine_number": "B18C12234567", "registration_date": "2018-09-20",  "city": "Mumbai", "state": "Maharashtra"},
    "2T1BR32E54C123456": {"owner_name": "Priya Verma", "chassis_number": "2T1BR32E54C123456", "engine_number": "1ZZFE8745632", "registration_date": "2019-03-12", "city": "MumDelhibai", "state": "Delhi"},
}

const getDataByChassis = async (chassis_number) => {
    return mock_vehicle_db[chassis_number] || null;
}

module.exports = { getDataByChassis }