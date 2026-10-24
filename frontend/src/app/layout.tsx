import "./globals.css";
import { AppSession } from "@/components/AppSession";
import { Nav } from "@/components/Nav";
const title = "EvalForge — Evidence before release";
const description = "Catch AI answers that cite the wrong evidence. Strict saved-response evaluation with reproducible, inspectable evidence bundles.";
export const metadata = {
    title,
    description,
    openGraph: {
        title,
        description,
        type: "website",
        siteName: "EvalForge",
    },
    twitter: {
        card: "summary",
        title,
        description,
    },
};
export default function RootLayout({ children }: {
    children: React.ReactNode;
}) { return <html lang="en"><body><AppSession><Nav />{children}</AppSession></body></html>; }
