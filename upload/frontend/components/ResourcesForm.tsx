import ComboboxFormField from "@/components/ComboboxFormField";

export default function ResourcesForm({ form }) {
  return (
    <div className="space-y-4">
      {/* CPU Cores */}
      <ComboboxFormField
        form={form}
        name="cpu"
        label="CPU Cores"
        description="Allocate CPU cores (1-64)"
        options={[
          { value: 1, label: "1 Core" },
          { value: 2, label: "2 Cores" },
          { value: 4, label: "4 Cores" },
          { value: 8, label: "8 Cores" },
          { value: 16, label: "16 Cores" },
          { value: 32, label: "32 Cores" },
          { value: 64, label: "64 Cores" },
        ]}
      />

      {/* Memory */}
      <ComboboxFormField
        form={form}
        name="memory"
        label="Memory"
        description="Allocate memory in GB (1-256)"
        options={[
          { value: 1, label: "1 GB" },
          { value: 2, label: "2 GB" },
          { value: 4, label: "4 GB" },
          { value: 8, label: "8 GB" },
          { value: 16, label: "16 GB" },
          { value: 32, label: "32 GB" },
          { value: 64, label: "64 GB" },
          { value: 128, label: "128 GB" },
          { value: 256, label: "256 GB" },
        ]}
      />

      {/* GPU Units */}
      <ComboboxFormField
        form={form}
        name="gpu"
        label="GPU Units"
        description="Allocate GPU units (0-8)"
        options={[
          { value: 0, label: "No GPU" },
          { value: 1, label: "1 GPU" },
          { value: 2, label: "2 GPUs" },
          { value: 4, label: "4 GPUs" },
          { value: 8, label: "8 GPUs" },
        ]}
      />
    </div>
  );
}
