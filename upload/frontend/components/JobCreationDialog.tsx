"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { z } from "zod";

import { steps } from "@/constants/steps";
import { formSchema } from "@/schemas/formSchema";
import { Form } from "@/components/ui/form";
import { Button } from "@/components/ui/button";

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { Plus } from "lucide-react";

import ProgressBar from "@/components/ProgressBar";

import BasicInfoForm from "@/components/BasicInfoForm";
import ResourcesForm from "@/components/ResourcesForm";
import AdvancedForm from "@/components/AdvancedForm";
import ReviewForm from "@/components/ReviewForm";

export default function JobCreationDialog() {
  const [currentStep, setCurrentStep] = useState(0);
  const [open, setOpen] = useState(false);
  const router = useRouter();

  // State for file upload
  const [codeFile, setCodeFile] = useState<File | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      jobShortName: "",
      description: "",
      jobType: "batch",
      cpu: 1,
      memory: 1,
      gpu: 0,
      envVars: [{ key: "", value: "" }],
    },
  });

  // Function to get the fields for each step dynamically
  const getStepFields = () => {
    switch (currentStep) {
      case 0:
        return ["jobName", "description", "jobType"];
      case 1:
        return ["cpu", "memory", "gpu"];
      case 2:
        const jobType = form.getValues("jobType");
        return jobType === "batch" ? ["envVars"] : ["envVars"];
      default:
        return [];
    }
  };

  const nextStep = async () => {
    const fields = getStepFields();
    const isValid = await form.trigger(fields);
    if (isValid) {
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      }
    } else {
      // Optionally, you can display a toast or message here
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  async function onSubmit(values: z.infer<typeof formSchema>) {
    if (!codeFile) {
      toast.error("Please upload a file.");
      return;
    }

    try {
      // Create FormData
      const formData = new FormData();
      formData.append("file", codeFile); // Add the file
      formData.append("job_name", values.jobShortName); // Add the job name

      // Send the FormData to the backend
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_SERVER_URL}/upload/`,
        {
          method: "POST",
          body: formData,
        },
      );

      const jobSubmissionData = await response.json();

      console.log(jobSubmissionData);

      if (!response.ok) {
        throw new Error(`Failed to submit job: ${response.statusText}`);
      }

      // Success notification
      toast("Job Created", {
        description: `Job "${jobSubmissionData.job_name}" has been submitted successfully.`,
        action: {
          label: "Go to Resource",
          onClick: () => {
            // Navigate to the dynamically generated route
            router.push(
              `/jobs/${jobSubmissionData.job_name}-kaniko-build-${jobSubmissionData.upload_id}`,
            );
          },
        },
      });

      // Reset the form and file input
      form.reset();
      setCodeFile(null);
      setOpen(false);
    } catch (error) {
      console.error("Error submitting job:", error);
      toast.error("Failed to submit job. Please try again.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="orange"
          className="h-8"
          onClick={() => {
            setOpen(true);
            setCurrentStep(0); // Reset to the first step when opening the modal
            form.reset(); // Reset form values
            setCodeFile(null); // Reset file state
          }}
        >
          New Job <Plus strokeWidth={2} />
        </Button>
      </DialogTrigger>
      <DialogContent className="w-full max-w-4xl h-[700px] mx-auto flex flex-col">
        <div className="w-full max-w-4xl h-full mx-auto flex flex-col">
          <DialogHeader>
            <DialogTitle className="hidden">Create a Job</DialogTitle>
            <ProgressBar
              currentStep={currentStep}
              setCurrentStep={setCurrentStep}
            />
          </DialogHeader>
          <div className="h-full">
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="h-full grid grid-rows-[1fr_auto] gap-8"
              >
                {/* Form Content */}
                <div className="overflow-auto px-2 p-4">
                  {currentStep === 0 && <BasicInfoForm form={form} />}
                  {currentStep === 1 && <ResourcesForm form={form} />}
                  {currentStep === 2 && (
                    <AdvancedForm
                      form={form}
                      codeFile={codeFile}
                      setCodeFile={setCodeFile}
                    />
                  )}
                  {currentStep === 3 && <ReviewForm form={form} />}
                </div>

                {/* Buttons */}
                <div className="flex justify-between items-center">
                  {currentStep > 0 && (
                    <div>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={prevStep}
                      >
                        Previous
                      </Button>
                    </div>
                  )}
                  <div className="ml-auto">
                    {currentStep < steps.length - 1 ? (
                      <Button type="button" onClick={nextStep}>
                        Next
                      </Button>
                    ) : (
                      <DialogFooter className="sm:justify-start">
                        <Button
                          className="bg-blue-500 font-bold hover:bg-blue-600"
                          type="submit"
                        >
                          Create Job
                        </Button>
                      </DialogFooter>
                    )}
                  </div>
                </div>
              </form>
            </Form>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
