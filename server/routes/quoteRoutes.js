import express from "express";
import rateLimit from "express-rate-limit";
import Quote from "../models/Quote.js";
import { requireAdmin } from "../middleware/auth.js";
import { dispatchQuoteEmails } from "../utils/mailer.js";

const router = express.Router();

const quoteLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // max 5 quote submissions per IP per 15 mins
  message: { error: "Too many requests. Please try again in 15 minutes." },
});

// PUBLIC: Submit new B2B quote
router.post("/", quoteLimiter, async (req, res) => {
  try {
    const {
      fullName,
      companyName,
      email,
      phone,
      serviceType,
      location,
      estimatedValueINR,
      projectNotes,
    } = req.body;

    if (!fullName || !companyName || !email || !phone || !serviceType) {
      return res.status(400).json({ error: "All required fields must be filled." });
    }

    const randomCode = Math.floor(1000 + Math.random() * 9000);
    const referenceId = `VG-${new Date().getFullYear()}-${randomCode}`;

    const newQuote = await Quote.create({
      referenceId,
      fullName,
      companyName,
      email,
      phone,
      serviceType,
      location,
      estimatedValueINR: Number(estimatedValueINR) || 0,
      projectNotes,
    });

    // Fire emails without blocking HTTP response
    dispatchQuoteEmails(newQuote).catch((err) =>
      console.error("Email dispatch error:", err.message)
    );

    res.status(201).json({
      message: "Quote request logged successfully.",
      referenceId: newQuote.referenceId,
    });
  } catch (err) {
    console.error("Quote creation failed:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

// ADMIN: List all leads
router.get("/", requireAdmin, async (req, res) => {
  try {
    const quotes = await Quote.find().sort({ createdAt: -1 });
    res.json(quotes);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch quotes" });
  }
});

// ADMIN: Update deal stage or notes
router.patch("/:id", requireAdmin, async (req, res) => {
  try {
    const { status, adminNotes } = req.body;
    const updated = await Quote.findByIdAndUpdate(
      req.params.id,
      { ...(status && { status }), ...(adminNotes !== undefined && { adminNotes }) },
      { new: true }
    );
    if (!updated) return res.status(404).json({ error: "Lead not found" });
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: "Failed to update lead" });
  }
});

export default router;