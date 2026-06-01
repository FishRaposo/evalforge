import './globals.css';

export const metadata = {
  title: 'EvalForge Dashboard',
  description: 'AI evaluation and compliance analytics',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-900 text-slate-200">
        {children}
      </body>
    </html>
  );
}
