// src/pages/Dashboard.jsx
import React, { useEffect, useState, useRef } from "react";
import { getDocuments, uploadPdf } from "../services/api";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:3000"; // same origin; or "http://localhost:3000" during dev

const Dashboard = () => {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const socketRef = useRef(null);

  useEffect(() => {
    // initial fetch
    fetchDocs();

    // connect socket
    socketRef.current = io(SOCKET_URL, { transports: ["websocket"] });

    socketRef.current.on("connect", () => {
      console.log("Connected to socket:", socketRef.current.id);
    });

    socketRef.current.on("documentProcessed", ({ jobId, payload }) => {
      console.log("Realtime - documentProcessed:", jobId, payload);

      socketRef.current.on("verificationTriggered", (data) => {
        setMessage(data.message);
      });

      socketRef.current.on("verificationCompleted", (data) => {
        setMessage(data.message);
      });

      socketRef.current.on("verificationFailed", (data) => {
        setMessage(data.message);
      });


      // Insert incoming payload at beginning of list
      setDocuments(prev => {
        // if payload has customer_id make sure not to duplicate
        if (!payload) return prev;
        const exists = prev.some(d => d.customer_id && payload.customer_id && d.customer_id === payload.customer_id);
        if (exists) {
          // replace existing entry
          return prev.map(d => (d.customer_id === payload.customer_id ? payload : d));
        }
        return [payload, ...prev];
      });

      setMessage(`Document processed for job ${jobId}`);
      // optionally clear after few seconds
      setTimeout(() => setMessage(""), 5000);
    });

    socketRef.current.on("dbChanged", (payload) => {
      if (!payload) return;
      const { type, data } = payload;

      setDocuments((prev) => {
        if (type === "insert") return [data, ...prev];
        if (type === "update") return prev.map(d => d.customer_id === data.customer_id ? data : d);
        if (type === "delete") return prev.filter(d => d.customer_id !== data.customer_id);
        return prev;
      });
    });

    socketRef.current.on("disconnect", () => console.log("Socket disconnected"));

    // cleanup
    return () => {
      if (socketRef.current) socketRef.current.disconnect();
    };
  }, []);

  const fetchDocs = async () => {
    try {
      const res = await getDocuments();
      setDocuments(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    const file = e.target.elements.pdf.files[0];
    if (!file) return alert("Select a file");
    setUploading(true);
    try {
      const response = await uploadPdf(file);
      setMessage(`Upload accepted (job ${response.jobId}). Processing in background.`);
      // do NOT wait for processing — wait for socket event
    } catch (err) {
      console.error(err);
      setMessage(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      // clear file input
      e.target.reset();
      setTimeout(() => setMessage(""), 5000);
    }
  };

  return (

    <div className="container">
      <aside className="sidebar">
        <div className="logo">DCP</div>
        <nav>
          <ul>
            <li className="active">Dealer Claim Form After Sales Flow 1</li>
            <li>Dealer Claim Form After Sales Flow 2</li>
            <li>Dealer Statements</li>
            <li>Temp Dealer Statement New</li>
            <li>Sales Outlet</li>
          </ul>
        </nav>
      </aside>

      <div className="dashboard-container">
        <header>
          <h1>Document Verification Dashboard</h1>
          {message && <div id="uploadStatus">{message}</div>}
        </header>

        <section className="upload-section">
          <form onSubmit={handleUpload}>
            <label htmlFor="pdfUpload">Upload PDF:</label>
            <input type="file" id="pdfUpload" name="pdf" accept="application/pdf" />
            <button id="uploadBtn" type="submit" disabled={uploading}>
              {uploading ? "Uploading..." : "Upload PDF"}
            </button>
          </form>
        </section>

        <section className="table-section">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Filename</th>
                  <th>Name</th>
                  <th>DOB</th>
                  <th>Gender</th>
                  <th>Address</th>
                  <th>City</th>
                  <th>State</th>
                  <th>Aadhaar</th>
                  <th>Permanent Account Number</th>
                  <th>Driving License</th>
                  <th>Registration Certificate</th>
                  <th>Sales Tax Invoice</th>
                  <th>Delivery Acknowledgement Note</th>
                  <th>Customer Discount Declaration</th>
                  <th>Customer Verification</th>
                  <th>Vehicle Verification</th>
                  <th>Status</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((d, idx) => (
                  <tr key={d.customer_id || idx}>
                    <td>{d.customer_id}</td>
                    <td>{d.filename}</td>
                    <td>{d.name}</td>
                    <td>{new Date(d.dob).toLocaleDateString("en-GB")}</td>
                    <td>{d.gender}</td>
                    <td>{d.address}</td>
                    <td>{d.city}</td>
                    <td>{d.state}</td>
                    <td>{d.aadhaar_provided ? d.aadhaar_number : "Aadhaar Not Present"}</td>
                    <td>{d.pan_provided ? d.pan_number : "PAN Not Present"}</td>
                    <td>{d.dl_provided ? d.dl_number : "DL Not Present"}</td>
                    <td>{d.rc_provided ? d.vehicle_rc : "No"}</td>
                    <td>VIN: {d.tvin_number} <br /> Engine No.: {d.tengine_number} <br /> Chassis No.: {d.tchassis_number}</td>
                    <td>VIN: {d.dvin_number} <br /> Engine No.: {d.dengine_number} <br /> Chassis No.: {d.dchassis_number}</td>
                    <td>VIN: {d.cvin_number} <br /> Engine No.: {d.cengine_number} <br /> Chassis No.: {d.cchassis_number}</td>
                    <td>{d.customer_verification ? "verified" : "unverified"}</td>
                    <td>{d.vehicle_verification ? "verified" : "unverified"}</td>
                    <td>{d.verification_status}</td>
                    <td>{d.verification_result ? "Present" : "Not present"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>

  );
};

export default Dashboard;
