import { Book, Brain, FileText, Zap } from "lucide-react";

export function StudyModeButtons() {
  const modes = [
    { icon: Brain, label: "Học", color: "hover:bg-green-50" },
    { icon: FileText, label: "Kiểm tra", color: "hover:bg-purple-50" },
  ];

  return (
    <div className="grid grid-cols-2 border-t border-slate-200">
      {modes.map((mode, index) => (
        <button
          key={mode.label}
          className={`flex flex-col items-center justify-center gap-1 py-3 ${mode.color} transition-colors ${
            index !== modes.length - 1 ? "border-r border-slate-200" : ""
          }`}
        >
          <mode.icon className="size-5 text-slate-700" />
          <span className="text-slate-700 text-xs">{mode.label}</span>
        </button>
      ))}
    </div>
  );
}