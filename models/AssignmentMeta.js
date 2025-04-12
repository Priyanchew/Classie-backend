const mongoose = require('mongoose');

const assignmentMetaSchema = new mongoose.Schema({
  title: String,
  description: String,
  dueDate: Date,
  createdBy: String
});

module.exports = mongoose.model('AssignmentMeta', assignmentMetaSchema);
