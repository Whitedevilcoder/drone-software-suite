import nodemailer from "nodemailer";

export async function dispatchQuoteEmails(quote) {
  if (!process.env.SMTP_USER || !process.env.SMTP_PASS) {
    console.warn("[MAILER] SMTP_USER or SMTP_PASS missing — skipping email dispatch.");
    return;
  }

  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || "smtp.gmail.com",
    port: Number(process.env.SMTP_PORT) || 587,
    secure: false,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });

  const founderMail = transporter.sendMail({
    from: `"VayuGrid Lead Engine" <${process.env.SMTP_USER}>`,
    to: process.env.FOUNDER_ALERT_EMAIL || process.env.SMTP_USER,
    subject: `[NEW LEAD ${quote.referenceId}] ${quote.companyName} — ₹${quote.estimatedValueINR.toLocaleString("en-IN")}`,
    html: `
      <div style="font-family: monospace; background: #070B14; color: #E2E8F0; padding: 20px; border-radius: 8px;">
        <h2 style="color: #06B6D4; margin-top: 0;">NEW B2B QUOTE REQUEST (${quote.referenceId})</h2>
        <p><strong>Contact:</strong> ${quote.fullName} (${quote.companyName})</p>
        <p><strong>Phone:</strong> ${quote.phone}</p>
        <p><strong>Email:</strong> ${quote.email}</p>
        <p><strong>Service:</strong> ${quote.serviceType}</p>
        <p><strong>Location:</strong> ${quote.location}</p>
        <p><strong>Est. Value:</strong> ₹${quote.estimatedValueINR.toLocaleString("en-IN")}</p>
        <hr style="border-color: #1E293B;" />
        <p><strong>Notes:</strong><br/>${quote.projectNotes || "N/A"}</p>
      </div>
    `,
  });

  const clientMail = transporter.sendMail({
    from: `"VayuGrid Aerospace" <${process.env.SMTP_USER}>`,
    to: quote.email,
    subject: `Quote Request Received [${quote.referenceId}] — VayuGrid Aerospace`,
    html: `
      <div style="font-family: sans-serif; color: #0F172A; line-height: 1.6;">
        <h3>Hello ${quote.fullName},</h3>
        <p>We have logged your inquiry for <strong>${quote.companyName}</strong> under reference ID <strong>${quote.referenceId}</strong>.</p>
        <p>Our engineering and aerial data operations team will respond within <strong>24 business hours</strong>.</p>
      </div>
    `,
  });

  await Promise.allSettled([founderMail, clientMail]);
}