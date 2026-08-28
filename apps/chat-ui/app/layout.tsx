import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LearnAgenticAI Chat",
  description: "Chat UI for LearnAgenticAI agents",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
