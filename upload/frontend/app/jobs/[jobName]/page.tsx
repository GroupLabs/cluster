"use client";

import {
  CheckCircle,
  AlertCircle,
  Info,
  LoaderCircle,
  RefreshCw,
  Copy,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

const statuses = {
  pending: {
    name: "Pending",
    icon: LoaderCircle,
    iconColor: "text-yellow-500",
  },
  created: {
    name: "Created",
    icon: Info,
    iconColor: "text-purple-500",
  },
  running: {
    name: "Running",
    icon: RefreshCw,
    iconColor: "text-blue-500",
  },
  complete: {
    name: "Complete",
    icon: CheckCircle,
    iconColor: "text-green-500",
  },
  error: {
    name: "Error",
    icon: AlertCircle,
    iconColor: "text-red-500",
  },
};

export default function JobDetailPage() {
  const { jobName } = useParams();

  const [jobHistory, setJobHistory] = useState([]);
  const [jobData, setJobData] = useState({
    job_name: "",
    namespace: "default",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [logs, setLogs] = useState(""); // State for pod logs
  const [isLogsLoading, setIsLogsLoading] = useState(true); // State for logs loading

  useEffect(() => {
    if (!jobName) return;

    async function fetchJobHistory() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_SERVER_URL}/jobs/${jobName}/history`,
        );
        if (!response.ok) {
          throw new Error(
            `Failed to fetch job history: ${response.statusText}`,
          );
        }
        const data = await response.json();

        const mappedHistory = data.history.map((event, idx) => {
          const eventDate = new Date(event.timestamp);
          return {
            id: idx,
            type: event.status.toLowerCase(),
            message: event.message,
            date: eventDate.toLocaleDateString(),
            time: eventDate.toLocaleTimeString(),
            dateTime: event.timestamp,
          };
        });

        setJobData({ job_name: data.job_name, namespace: "default" });
        setJobHistory(mappedHistory);
      } catch (error) {
        console.error("Error fetching job history:", error);
        setJobHistory([]);
      } finally {
        setIsLoading(false);
      }
    }

    async function fetchPodLogs() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_SERVER_URL}/jobs/${jobName}/logs`,
        );
        if (!response.ok) {
          throw new Error(`Failed to fetch pod logs: ${response.statusText}`);
        }
        const data = await response.json();
        setLogs(data.logs);
      } catch (error) {
        console.error("Error fetching pod logs:", error);
        setLogs("Failed to fetch logs.");
      } finally {
        setIsLogsLoading(false);
      }
    }

    fetchJobHistory();
    fetchPodLogs();
  }, [jobName]);

  const handleSshConnect = async () => {
    const sshCommand = `ssh user@host -p 22 # For job: ${jobData.job_name}`;
    try {
      await navigator.clipboard.writeText(sshCommand);
      toast("SSH Command Copied", {
        description: `The SSH command has been copied to your clipboard.`,
      });
    } catch (error) {
      console.error("Failed to copy SSH command:", error);
      toast("Error", {
        description: `Failed to copy SSH command to clipboard.`,
      });
    }
  };

  const handleJupyterConnect = async () => {
    const jupyterUrl = `http://jupyter-notebook-host:8888/?token=your_token_here`; // Placeholder URL
    try {
      await navigator.clipboard.writeText(jupyterUrl);
      toast("Jupyter Notebook URL Copied", {
        description: `The Jupyter Notebook URL has been copied to your clipboard.`,
      });
    } catch (error) {
      console.error("Failed to copy Jupyter URL:", error);
      toast("Error", {
        description: `Failed to copy Jupyter Notebook URL to clipboard.`,
      });
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Job: {jobData.job_name || "Loading..."}
          </h2>
          <p className="text-sm text-gray-600">
            Namespace: {jobData.namespace || "Loading..."}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={handleSshConnect} variant={"outline"}>
            SSH <Copy />
          </Button>
          <Button onClick={handleJupyterConnect} variant="orange">
            Jupyter Notebook <Copy />
          </Button>
        </div>
      </div>
      {isLoading ? (
        <div className="mt-6 text-gray-500 text-center">Loading history...</div>
      ) : (
        <ul role="list" className="mt-6 space-y-6">
          {jobHistory.map((event, idx) => {
            const Icon = statuses[event.type]?.icon || Info;

            return (
              <li key={event.id} className="relative flex gap-x-4">
                <div
                  className={cn(
                    idx === jobHistory.length - 1 ? "h-6" : "-bottom-6",
                    "absolute left-0 top-0 flex w-6 justify-center",
                  )}
                >
                  <div className="w-px bg-gray-200" />
                </div>
                <div className="relative flex h-6 w-6 flex-none items-center justify-center bg-white">
                  <Icon
                    aria-hidden="true"
                    className={cn("h-6 w-6", statuses[event.type]?.iconColor)}
                  />
                </div>
                <div className="flex-auto">
                  <div className="flex justify-between gap-x-4">
                    <p className="text-sm text-gray-900">
                      {statuses[event.type]?.name || "Unknown"}
                    </p>
                    <time
                      dateTime={event.dateTime}
                      className="flex-none text-xs text-gray-500"
                    >
                      {event.date} {event.time}
                    </time>
                  </div>
                  <p className="mt-0.5 text-sm text-gray-500">
                    {event.message}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
      <div className="mt-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Pod Logs</h3>
        {isLogsLoading ? (
          <div className="text-gray-500">Loading logs...</div>
        ) : (
          <pre className="bg-gray-100 p-4 rounded-md overflow-auto text-sm text-gray-800">
            {logs}
          </pre>
        )}
      </div>
    </div>
  );
}
