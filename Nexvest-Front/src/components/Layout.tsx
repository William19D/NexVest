import { ReactNode } from "react";
import AppSidebar from "./AppSidebar";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-background bg-grid">
      <AppSidebar />
      <main className="ml-16 flex-1 lg:ml-56">
        <div className="p-4 lg:p-6">{children}</div>
      </main>
    </div>
  );
}
