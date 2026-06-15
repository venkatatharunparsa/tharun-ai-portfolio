import "./globals.css";

export const metadata = {
  title: "Tharun AI — Agentic Voice Portfolio",
  description:
    "Venkata Tharun Parsa — Agentic AI Engineer. Talk to Tharun AI to learn about his projects, skills, and experience.",
  keywords: "Agentic AI, LangGraph, RAG, Voice AI, Portfolio, Tharun Parsa",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
