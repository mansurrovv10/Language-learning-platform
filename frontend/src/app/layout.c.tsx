import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppSidebar } from "@/components/app-sibar";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
      <body>
        <TooltipProvider>
          <SidebarProvider>
            <AppSidebar />
            <main className="w-full p-6">
              <SidebarTrigger />
              {children}
            </main>
          </SidebarProvider>
        </TooltipProvider>
      </body>
  );
}
