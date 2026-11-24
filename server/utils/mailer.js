import nodemailer from "nodemailer";

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: Number(process.env.SMTP_PORT) || 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

export async function dispatchQuoteEmails(quote) {
  // 1. Instant Founder Notification
  const founderMail = transporter.sendMail({
    from: `"VayuGrid Lead Engine" <${process.env.SMTP_USER}>`,
    to: process.env.FOUNDER_ALERT_EMAIL,
    subject: `[NEW LEAD ${quote.referenceId}] ${quote.companyName} — ₹${quote.estimatedValueINR.toLocaleString("en-IN")}`,
    html: `
      <div style="font-family: monospace; background: #070B14; color: #E2E8F0; padding: 20px; border-radius: 8px;">
        <h2 style="color: #06B6D4; margin-top: 0;">NEW B2B QUOTE REQUEST (${quote.referenceId})</h2>
        <p><strong>Contact:</strong> ${quote.fullName} (${quote.companyName})</p>
        <p><strong>Phone:</strong> <a href="tel:${quote.phone}" style="color: #F59E0B;">${quote.phone}</a></p>
        <p><strong>Email:</strong> ${quote.email}</p>
        <p><strong>Service:</strong> ${quote.serviceType}</p>
        <p><strong>Site Location:</strong> ${quote.location}</p>
        <p><strong>Est. Value:</strong> ₹${quote.estimatedValueINR.toLocaleString("en-IN")}</p>
        <hr style="border-color: #1E293B;" />
        <p><strong>Scope / Notes:</strong><br/>${quote.projectNotes || "N/A"}</p>
      </div>
    `,
  });

  // 2. Automated Client Confirmation
  const clientMail = transporter.sendMail({
    from: `"VayuGrid Aerospace" <${process.env.SMTP_USER}>`,
    to: quote.email,
    subject: `Quote Request Received [${quote.referenceId}] — VayuGrid Aerospace`,
    html: `
      <div style="font-family: sans-serif; color: #0F172A; line-height: 1.6;">
        <h3>Hello ${quote.fullName},</h3>
        <p>We have logged your inquiry for <strong>${quote.companyName}</strong> under reference ID <strong>${quote.referenceId}</strong>.</p>
        <p>Our engineering and aerial data operations team will review your site parameters and respond within <strong>24 business hours</strong> with a commercial proposal.</p>
        <p style="font-size: 13px; color: #475569;">For urgent plant shutdowns or same-day raw dataset uploads, reply directly to this email.</p>
      </div>
    `,
  });

  await Promise.allSettled([founderMail, clientMail]);
}