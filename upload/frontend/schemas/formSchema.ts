import { z } from "zod";

export const formSchema = z
  .object({
    jobShortName: z.string().min(3, {
      message: "Job name must be at least 3 characters.",
    }),
    description: z.string().optional(),
    jobType: z.enum(["batch", "interactive"]),
    cpu: z.number().min(1).max(64),
    memory: z.number().min(1).max(256),
    gpu: z.number().min(0).max(8),
    notificationEmail: z.string().email().optional(),
    codeFile: z.instanceof(File).nullable().optional(),
    envVars: z
      .array(
        z.object({
          key: z.string(),
          value: z.string(),
        }),
      )
      .optional(),
  })
  .refine(
    (data) => {
      if (data.jobType === "batch" && !data.codeFile) {
        return false; // For batch jobs, a file is required
      }
      if (data.codeFile && data.jobType === "batch") {
        return data.codeFile.type === "application/zip";
      }
      return true;
    },
    {
      path: ["codeFile"],
      message: "For batch jobs, a .zip code archive is required.",
    },
  );
