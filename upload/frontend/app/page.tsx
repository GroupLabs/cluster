"use client";

import Head from "next/head";
import { useState, useEffect } from "react";
import { columns } from "@/components/ui/connector-table/columns";
import { DataTable } from "@/components/ui/connector-table/data-table";

export default function Home() {
  const [jobsData, setJobsData] = useState(null);

  function mapJobStatus(
    status: string,
  ): "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" {
    switch (status) {
      case "Running": // Kubernetes status indicating the Job is running
        return "STARTED";
      case "Completed": // Kubernetes status indicating the Job completed successfully
        return "SUCCESS";
      case "Failed": // Kubernetes status indicating the Job failed
        return "FAILURE";
      default: // Any other status or lack of status indicates pending
        return "PENDING";
    }
  }

  useEffect(() => {
    async function fetchJobs() {
      try {
        const response = await fetch(
          process.env.NEXT_PUBLIC_SERVER_URL + "/jobs",
        );
        if (!response.ok) {
          throw new Error(`Error fetching jobs: ${response.statusText}`);
        }
        const data = await response.json();

        // Map the data to the format expected by DataTable
        const mappedData = data.jobs.map((job) => {
          // Extract title, label, and id from job name
          const jobNameParts = job.name.split("-");
          // Assuming the job name format is <title>-<label>-<id>

          const title = jobNameParts[0]; // First part is the title
          const label = jobNameParts.slice(1, -5).join("-"); // Middle parts are the label
          const id = jobNameParts.slice(-5).join("-"); // Last 5 parts form the UUID

          console.log(job.status);

          // Get the status
          const status = mapJobStatus(job.status); // e.g., "Unknown", "Completed", etc.

          // TTL
          const ttl = job.ttl;

          return {
            label,
            title,
            id,
            status,
            ttl,
          };
        });

        console.log(mappedData);
        setJobsData(mappedData);
      } catch (error) {
        console.error("Error fetching jobs:", error);
        setJobsData([]); // Handle the error appropriately
      }
    }

    fetchJobs();
  }, []);

  return (
    <>
      <Head>
        <title>Home</title>
        <meta name="Home" content="Deploy your jobs, powered by GroupLabs" />
      </Head>
      <div className="w-full h-screen flex items-center justify-center">
        <div className="w-[90%]">
          {jobsData ? (
            <DataTable data={jobsData} columns={columns} />
          ) : (
            <div>Loading...</div>
          )}
        </div>
      </div>
    </>
  );
}
