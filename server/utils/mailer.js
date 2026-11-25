import nodemailer from "nodemailer";

async function sendViaBrevo({ toEmail, toName, subject, html }) {
  const senderEmail = process.env.SENDER_EMAIL || process.env.SMTP_USER;
  const res = await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: {
      accept: "application/json",
      "api-key": process.env.BREVO_API_KEY,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      sender: { name: "VayuGrid Aerospace", email: senderEmail },
      to: [{ email: toEmail, name: toName || toEmail }],
      subject,
      htmlContent: html,
    }),
  });

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(`Brevo HTTP ${res.status}: ${errBody}`);
  }
}

async function sendViaSmtp({ toEmail, subject, html }) {
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || "smtp.gmail.com",
    port: Number(process.env.SMTP_PORT) || 587,
    secure: Number(process.env.SMTP_PORT) === 465,
    connectionTimeout: 10000,
    greetingTimeout: 10000,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });

  await transporter.sendMail({
    from: `"VayuGrid Aerospace" <${process.env.SMTP_USER}>`,
    to: toEmail,
    subject,
    html,
  });
}

async function deliverEmail(payload) {
  if (process.env.BREVO_API_KEY) {
    return sendViaBrevo(payload);
  }
  if (process.env.SMTP_USER && process.env.SMTP_PASS) {
    return sendViaSmtp(payload);
  }
  throw new Error("No email provider configured (set BREVO_API_KEY or SMTP_USER/SMTP_PASS).");
}

export async function dispatchQuoteEmails(quote) {
  const founderEmail =
    process.env.FOUNDER_ALERT_EMAIL || process.env.SENDER_EMAIL || process.env.SMTP_USER;

  const founderPayload = {
    toEmail: founderEmail,
    toName: "VayuGrid Ops",
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
  };

  const clientPayload = {
    toEmail: quote.email,
    toName: quote.fullName,
    subject: `Quote Request Received [${quote.referenceId}] — VayuGrid Aerospace`,
    html: `
      <div style="font-family: sans-serif; color: #0F172A; line-height: 1.6;">
        <h3>Hello ${quote.fullName},</h3>
        <p>We have logged your inquiry for <strong>${quote.companyName}</strong> under reference ID <strong>${quote.referenceId}</strong>.</p>
        <p>Our engineering and aerial data operations team will respond within <strong>24 business hours</strong>.</p>
      </div>
    `,
  };

  const results = await Promise.allSettled([
    deliverEmail(founderPayload),
    deliverEmail(clientPayload),
  ]);

  results.forEach((result, idx) => {
    const target = idx === 0 ? `Founder (${founderEmail})` : `Client (${quote.email})`;
    if (result.status === "rejected") {
      console.error(`[MAILER FAILED] ${target}:`, result.reason?.message || result.reason);
    } else {
      console.log(`[MAILER OK] Sent to ${target}`);
    }
  });
}