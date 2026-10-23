"use client";
import { useSession } from "./AppSession";
export function ConnectionError({ message, retry }: {
    message: string;
    retry: () => void;
}) { const { setMode } = useSession(); return <div className="error-panel" role="alert"><h2>Connected API unavailable</h2><p>{message}</p><p>Your current view has no sample substitute. Start the local API, then retry, or explicitly explore the sample.</p><div className="actions"><button onClick={retry}>Retry connection</button><button className="secondary" onClick={() => setMode("sample")}>Enter sample mode</button></div></div>; }
