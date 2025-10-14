import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pathio - Job Search & Application Assistant",
  description: "Find jobs and get tailored resumes and cover letters",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
