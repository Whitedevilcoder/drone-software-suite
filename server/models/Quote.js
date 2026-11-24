import mongoose from "mongoose";

const quoteSchema = new mongoose.Schema(
  {
    referenceId: { type: String, required: true, unique: true },
    fullName: { type: String, required: true, trim: true },
    companyName: { type: String, required: true, trim: true },
    email: { type: String, required: true, lowercase: true, trim: true },
    phone: { type: String, required: true, trim: true },
    serviceType: {
      type: String,
      enum: [
        "WHITE_LABEL_DATA_PROCESSING",
        "MINING_STOCKPILE_3D",
        "THERMAL_SOLAR_AUDIT",
        "CONFINED_SPACE_INSPECTION",
        "CUSTOM_UAV_RND",
      ],
      required: true,
    },
    location: { type: String, default: "Chhattisgarh / Central India", trim: true },
    estimatedValueINR: { type: Number, default: 0 },
    projectNotes: { type: String, maxlength: 2000, default: "" },
    status: {
      type: String,
      enum: ["NEW", "CONTACTED", "PROPOSAL_SENT", "WON", "LOST"],
      default: "NEW",
    },
    adminNotes: { type: String, default: "" },
  },
  { timestamps: true }
);

export default mongoose.model("Quote", quoteSchema);