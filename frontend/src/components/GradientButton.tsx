import type { ButtonHTMLAttributes, ReactNode } from "react";

interface GradientButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "emerald" | "cyan" | "red";
}

const VARIANTS = {
  emerald: "bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 shadow-glow",
  cyan:    "bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-600 hover:to-emerald-600",
  red:     "bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700",
};

export default function GradientButton({ children, variant = "emerald", className = "", ...props }: GradientButtonProps) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-white text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
    >
      {children}
    </button>
  );
}
