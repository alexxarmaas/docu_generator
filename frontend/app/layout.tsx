import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Docu Generator",
  description: "Workspace local para documentación de producto",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
