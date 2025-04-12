const express = require('express');
const router = express.Router();
const Student = require('../models/Student');
const AssignmentMeta = require('../models/AssignmentMeta');
const AssignmentSubmission = require('../models/AssignmentSubmission');

router.post('/student', async (req, res) => {
  const student = new Student(req.body);
  await student.save();
  res.json(student);
});

router.post('/assignment', async (req, res) => {
  const meta = new AssignmentMeta(req.body);
  await meta.save();
  res.json(meta);
});

router.post('/submit', async (req, res) => {
  const submission = new AssignmentSubmission(req.body);
  await submission.save();
  res.json(submission);
});

router.get('/submissions', async (req, res) => {
  const data = await AssignmentSubmission.find().populate('assignmentId');
  res.json(data);
});

module.exports = router;
