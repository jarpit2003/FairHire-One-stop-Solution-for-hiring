import { type ReactNode } from "react";
import Navbar from "./Navbar";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="pt-28 px-6 pb-6">
        <div className="page-content mx-auto">
          {children}
        </div>
      </main>
    </>
  );
}
