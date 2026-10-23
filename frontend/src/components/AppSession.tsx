"use client";
import { createContext, useContext, useState, useSyncExternalStore, type ReactNode, type Dispatch, type SetStateAction } from "react";
import type { DataMode } from "@/lib/api";
import { INITIAL_SAMPLE } from "@/lib/demo-scenarios";
interface Session {
    mode: DataMode;
    ready: boolean;
    setMode: (mode: DataMode) => void;
    sample: typeof INITIAL_SAMPLE;
    setSample: Dispatch<SetStateAction<typeof INITIAL_SAMPLE>>;
    epoch: number;
    reset: () => void;
}
const Context = createContext<Session | null>(null);
const subscribeReady = () => () => { };
const getReady = () => true;
const serverReady = () => false;
function storedMode(): DataMode | null { try {
    return sessionStorage.getItem("evalforge.mode.v1") === "connected" ? "connected" : sessionStorage.getItem("evalforge.mode.v1") === "sample" ? "sample" : null;
}
catch {
    return null;
} }
function subscribeMode(listener: () => void) { window.addEventListener("evalforge-mode", listener); window.addEventListener("storage", listener); return () => { window.removeEventListener("evalforge-mode", listener); window.removeEventListener("storage", listener); }; }
const serverMode = () => null;
export function AppSession({ children }: {
    children: ReactNode;
}) {
    const [volatileMode, changeMode] = useState<DataMode>("sample");
    const persistedMode = useSyncExternalStore(subscribeMode, storedMode, serverMode);
    const ready = useSyncExternalStore(subscribeReady, getReady, serverReady);
    const mode = persistedMode || volatileMode;
    const [sample, setSample] = useState({ ...INITIAL_SAMPLE });
    const [epoch, setEpoch] = useState(0);
    function setMode(value: DataMode) { changeMode(value); setEpoch(x => x + 1); try {
        sessionStorage.setItem("evalforge.mode.v1", value);
        window.dispatchEvent(new Event("evalforge-mode"));
    }
    catch { /* In-memory mode remains usable. */ } }
    function reset() { setSample({ ...INITIAL_SAMPLE }); setEpoch(x => x + 1); }
    return <Context.Provider value={{ mode, ready, setMode, sample, setSample, epoch, reset }}>{children}</Context.Provider>;
}
export function useSession() { const value = useContext(Context); if (!value)
    throw new Error("AppSession provider is required"); return value; }
