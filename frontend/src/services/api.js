// src/services/api.js
const BASE = "http://localhost:3000"; // same origin in production; for dev use "http://localhost:3000"

export const getDocuments = async () => {
  const res = await fetch(`${BASE}/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
};

export const uploadPdf = async (file) => {
  const form = new FormData();
  form.append("pdf", file);

  const res = await fetch(`${BASE}/uploadPDF`, {
    method: "POST",
    body: form
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Upload failed");
  }
  return res.json(); // { message, jobId, key }
};
