import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import helmet from "helmet";
import quoteRoutes from "./routes/quoteRoutes.js";
import authRoutes from "./routes/authRoutes.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, ".env") });

if (!process.env.MONGO_URI) {
  console.error("FATAL: MONGO_URI is missing in server/.env");
  process.exit(1);
}

const app = express();

const allowedOrigins = [
  "http://localhost:5173",
  "http://127.0.0.1:5173",
  ...(process.env.CLIENT_URL ? process.env.CLIENT_URL.split(",").map((u) => u.trim().replace(/\/+$/, "")) : []),
];

app.use(helmet());
app.use(
  cors({
    origin(origin, callback) {
      if (!origin || allowedOrigins.includes(origin)) {
        return callback(null, true);
      }
      return callback(new Error(`CORS blocked origin: ${origin}`));
    },
  })
);
app.use(express.json({ limit: "50kb" }));

app.get("/api/health", (req, res) => {
  res.status(200).json({ status: "OK", timestamp: new Date().toISOString() });
});

app.use("/api/auth", authRoutes);
app.use("/api/quotes", quoteRoutes);

const PORT = process.env.PORT || 5000;

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    console.log("[OK] Connected to MongoDB Atlas");
    app.listen(PORT, () => console.log(`[OK] Server listening on http://localhost:${PORT}`));
  })
  .catch((err) => {
    console.error("[FATAL] MongoDB connection error:", err.message);
    process.exit(1);
  });