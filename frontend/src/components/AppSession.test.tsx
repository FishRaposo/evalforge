import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { AppSession, useSession } from "./AppSession";
function Probe(){const {mode, setMode, sample, setSample, reset} = useSession(); return <><p>{mode}:{sample.scenario}:{sample.selectedCase}</p><button onClick={()=>setMode("connected")}>Connect</button><button onClick={()=>setSample({...sample, scenario:"error", selectedCase:"ef-adversarial-001"})}>Fault</button><button onClick={reset}>Reset</button></>;}
afterEach(()=>sessionStorage.clear());
it("persists mode across page mounts and resets the complete sample selection", async()=>{
 const view=render(<AppSession><Probe/></AppSession>);
 await waitFor(()=>expect(screen.getByText(/sample:baseline/)).toBeInTheDocument());
 fireEvent.click(screen.getByText("Fault")); expect(screen.getByText(/sample:error:ef-adversarial/)).toBeInTheDocument();
 fireEvent.click(screen.getByText("Reset")); expect(screen.getByText(/sample:baseline:ef-answerable-001/)).toBeInTheDocument();
 fireEvent.click(screen.getByText("Connect")); view.unmount(); render(<AppSession><Probe/></AppSession>);
 await waitFor(()=>expect(screen.getByText(/connected:baseline/)).toBeInTheDocument());
});
