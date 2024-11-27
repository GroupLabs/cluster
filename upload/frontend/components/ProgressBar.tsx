const steps = [
  { id: "Step 1", name: "Details", status: "complete" },
  { id: "Step 2", name: "Resources", status: "current" },
  { id: "Step 3", name: "Advanced", status: "upcoming" },
  { id: "Step 4", name: "Review", status: "upcoming" },
];

export default function ProgressBar({
  currentStep,
  setCurrentStep,
}: {
  currentStep: number;
  setCurrentStep: (step: number) => void;
}) {
  return (
    <nav aria-label="Progress">
      <ol role="list" className="space-y-4 md:flex md:space-x-8 md:space-y-0">
        {steps.map((step, index) => {
          // Determine step status dynamically based on currentStep
          const status =
            index < currentStep
              ? "complete"
              : index === currentStep
                ? "current"
                : "upcoming";

          return (
            <li key={step.id} className="md:flex-1">
              {status === "complete" ? (
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setCurrentStep(index);
                  }}
                  className="group flex flex-col border-l-4 border-blue-400 py-2 pl-4 hover:border-blue-600 md:border-l-0 md:border-t-4 md:pb-0 md:pl-0 md:pt-4"
                >
                  <span className="text-sm font-black text-blue-400 group-hover:text-blue-600">
                    {step.id}
                  </span>
                  <span className="text-sm font-medium">{step.name}</span>
                </a>
              ) : status === "current" ? (
                <a
                  href="#"
                  aria-current="step"
                  className="flex flex-col border-l-4 border-blue-500 py-2 pl-4 md:border-l-0 md:border-t-4 md:pb-0 md:pl-0 md:pt-4"
                >
                  <span className="text-sm font-black text-blue-500">
                    {step.id}
                  </span>
                  <span className="text-sm font-medium">{step.name}</span>
                </a>
              ) : (
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                  }}
                  className="group flex flex-col border-l-4 border-gray-200 py-2 pl-4 hover:border-gray-300 md:border-l-0 md:border-t-4 md:pb-0 md:pl-0 md:pt-4"
                >
                  <span className="text-sm font-medium text-gray-500 group-hover:text-gray-700">
                    {step.id}
                  </span>
                  <span className="text-sm font-medium">{step.name}</span>
                </a>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
