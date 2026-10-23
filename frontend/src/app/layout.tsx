import "./globals.css";
import { AppSession } from "@/components/AppSession";
import { Nav } from "@/components/Nav";
export const metadata = { title: "EvalForge — Evidence before release", description: "Catch AI answers that cite the wrong evidence." };
export default function RootLayout({ children }: {
    children: React.ReactNode;
}) { return <html lang="en"><body><AppSession><Nav />{children}</AppSession></body></html>; }
