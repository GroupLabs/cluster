export default function ReviewForm({ form }) {
  const values = form.getValues();
  const fileDetails = values.codeFile
    ? {
        name: values.codeFile.name,
        size: `${(values.codeFile.size / 1024).toFixed(2)} KB`,
        type: values.codeFile.type,
      }
    : null;

  return (
    <div className="space-y-4">
      <pre className="bg-muted text-sm p-4 rounded-md max-h-[480px] overflow-auto">
        {JSON.stringify(
          {
            ...values,
            codeFile: fileDetails || "No file uploaded",
          },
          null,
          2,
        )}
      </pre>
    </div>
  );
}
