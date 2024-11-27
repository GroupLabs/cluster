import { useState } from "react";
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import { MinusCircle, PlusCircle, Trash2 } from "lucide-react";
import { SiPytorch, SiNumpy, SiTensorflow, SiPandas } from "react-icons/si";

const libraryIcons: Record<string, { icon: JSX.Element; color: string }> = {
  pytorch: {
    icon: <SiPytorch className="inline-block" />,
    color: "bg-red-100 text-red-600",
  },
  numpy: {
    icon: <SiNumpy className="inline-block" />,
    color: "bg-blue-100 text-blue-600",
  },
  tensorflow: {
    icon: <SiTensorflow className="inline-block" />,
    color: "bg-orange-100 text-orange-600",
  },
  pandas: {
    icon: <SiPandas className="inline-block" />,
    color: "bg-green-100 text-green-600",
  },
};

export default function AdvancedForm({ form, codeFile, setCodeFile }) {
  const [detectedLibraries, setDetectedLibraries] = useState<
    Record<string, boolean>
  >({});

  const handleFileUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_SERVER_URL}/detect_libs`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("Server response:", data);

      // Parse the response and update detected libraries
      const dockerfileResults = data.results?.Dockerfile || {};
      setDetectedLibraries(dockerfileResults);
    } catch (error) {
      console.error("File upload failed:", error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCodeFile(file);
      form.setValue("codeFile", file);
      handleFileUpload(file);
    }
  };

  const handleEditFile = () => {
    setCodeFile(null);
    form.setValue("codeFile", undefined);
    setDetectedLibraries({});
  };

  return (
    <div className="space-y-4">
      {/* File Upload Section */}
      <FormField
        control={form.control}
        name="codeFile"
        render={({}) => (
          <FormItem>
            <FormLabel>Upload Code Archive</FormLabel>
            <FormControl>
              {codeFile ? (
                <div className="flex items-center justify-between bg-gray-100 p-2 rounded-md">
                  <p className="text-sm text-gray-700 pl-1">
                    <strong>{codeFile.name}</strong>
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleEditFile}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <Input
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                />
              )}
            </FormControl>
            {codeFile ? (
              <></>
            ) : (
              <FormDescription>
                Upload a zipped archive containing your code. Only `.zip` files
                are supported.
              </FormDescription>
            )}
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Detected Libraries Section */}
      <div className="max-h-[20px]">
        <ul className="flex space-x-4">
          {Object.entries(detectedLibraries).map(([library, detected]) =>
            detected ? (
              <li key={library} className="flex items-center space-x-2">
                {libraryIcons[library]?.icon || null}
                <span
                  className={`inline-flex items-center rounded-md max-h-[20px] px-2 py-1 text-xs font-medium ${
                    libraryIcons[library]?.color || "bg-gray-100 text-gray-600"
                  }`}
                >
                  {library}
                </span>
              </li>
            ) : null,
          )}
        </ul>
      </div>

      {/* Environment Variables */}
      <FormField
        control={form.control}
        name="envVars"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Environment Variables</FormLabel>
            <FormDescription>
              Add environment variables for your job.
            </FormDescription>
            <div className="max-h-[200px] overflow-y-auto -mx-2 -mb-2 px-2 pb-2">
              {field.value.map((envVar, index) => (
                <div key={index} className="flex items-center space-x-2 mt-2">
                  <Input
                    placeholder="Key"
                    value={envVar.key}
                    onChange={(e) => {
                      const newEnvVars = [...field.value];
                      newEnvVars[index].key = e.target.value;
                      field.onChange(newEnvVars);
                    }}
                  />
                  <Input
                    placeholder="Value"
                    value={envVar.value}
                    onChange={(e) => {
                      const newEnvVars = [...field.value];
                      newEnvVars[index].value = e.target.value;
                      field.onChange(newEnvVars);
                    }}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      const newEnvVars = field.value.filter(
                        (_, i) => i !== index,
                      );
                      field.onChange(newEnvVars);
                    }}
                  >
                    <MinusCircle className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
            <Button
              type="button"
              variant="outline"
              className="mt-2"
              onClick={() => {
                field.onChange([...field.value, { key: "", value: "" }]);
              }}
            >
              <PlusCircle className="h-4 w-4 mr-2" />
              Add Environment Variable
            </Button>
          </FormItem>
        )}
      />
    </div>
  );
}
