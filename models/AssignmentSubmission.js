const mongoose = require('mongoose');

const assignmentSubmissionSchema = new mongoose.Schema({
  studentId: String,
  assignmentId: { type: mongoose.Schema.Types.ObjectId, ref: 'AssignmentMeta' },
  content: String,
  version: Number,
  timestamp: { type: Date, default: Date.now }
});

assignmentSubmissionSchema.index({ studentId: 1, assignmentId: 1, version: 1 }, { unique: true });

module.exports = mongoose.model('AssignmentSubmission', assignmentSubmissionSchema);
