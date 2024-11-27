import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";

export default function BasicInfoForm({ form }) {
  return (
    <div className="space-y-4">
      {/* Job Name */}
      <FormField
        control={form.control}
        name="jobShortName"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Job Name</FormLabel>
            <FormControl>
              <Input placeholder="Enter job name" {...field} />
            </FormControl>
            <FormDescription>A unique name for your job.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Description */}
      <FormField
        control={form.control}
        name="description"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Description</FormLabel>
            <FormControl>
              <Textarea placeholder="Describe your job (optional)" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Job Type */}
      <FormField
        control={form.control}
        name="jobType"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Job Type</FormLabel>
            <Select onValueChange={field.onChange} defaultValue={field.value}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select a job type" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="batch">Batch</SelectItem>
                <SelectItem value="interactive">Interactive</SelectItem>
              </SelectContent>
            </Select>
            <FormDescription>
              Choose the type of job you want to run.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Email */}
      <FormField
        control={form.control}
        name="email"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Notification</FormLabel>
            <FormControl>
              <Input placeholder="Email (Optional)" {...field} />
            </FormControl>
            <FormDescription>
              An email to notify on job completion.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  );
}
