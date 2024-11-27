import { SiPandas, SiPytorch, SiTensorflow } from "react-icons/si";
import { FaPython } from "react-icons/fa";

export default function LibraryIcon({ library }) {
  switch (library) {
    case "pandas":
      return <SiPandas className="h-6 w-6 text-blue-500" />;
    case "pytorch":
      return <SiPytorch className="h-6 w-6 text-orange-500" />;
    case "tensorflow":
      return <SiTensorflow className="h-6 w-6 text-yellow-500" />;
    case "numpy":
      return <FaPython className="h-6 w-6 text-green-500" />;
    default:
      return null;
  }
}
