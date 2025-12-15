const express = require("express");
const path = require("path");
const { getPendingEntries } = require("../models/customersModel");

const redirectionController = {
  index: async (req, res) => {
    // res.send("This is the index page where the table interface will be displayed");
    let customerEntries = await getPendingEntries();
    // Render dashboard with processed data
    res.render("dashboard", { customerEntries });
  },
};

module.exports = redirectionController;
