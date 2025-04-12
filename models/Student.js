const mongoose = require('mongoose');

const studentSchema = new mongoose.Schema({
  studentId: { type: String, unique: true },
  name: String,
  email: String
});

module.exports = mongoose.model('Student', studentSchema);
