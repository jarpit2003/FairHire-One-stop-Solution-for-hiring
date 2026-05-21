import { motion } from "framer-motion";
import type { ReactNode } from "react";

export default function FadeIn({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
