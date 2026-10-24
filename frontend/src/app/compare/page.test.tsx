import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {afterEach,expect,it} from "vitest";
import {useState} from "react";
import {AppSession,useSession} from "@/components/AppSession";
import ComparePage from "./page";
function NavigationProbe(){const {sample,setSample,reset}=useSession();const [show,setShow]=useState(false);return <><button onClick={()=>{setSample({...sample,scenario:"repaired"});setShow(true);}}>Home repair then compare</button><button onClick={reset}>Reset demo</button><p>Shared scenario {sample.scenario}</p>{show?<ComparePage/>:null}</>;}
afterEach(()=>sessionStorage.clear());
it("keeps the chosen release and reset state consistent across overview and comparison",async()=>{
 render(<AppSession><NavigationProbe/></AppSession>);fireEvent.click(screen.getByText("Home repair then compare"));
 await waitFor(()=>expect(screen.getByLabelText("Current run")).toHaveValue("demo-repaired"));
 expect(screen.getAllByTestId("release-gate")[1]).toHaveTextContent("Contract passed");
 fireEvent.change(screen.getByLabelText("Current run"),{target:{value:"demo-7"}});expect(screen.getByText("Shared scenario candidate")).toBeInTheDocument();
 fireEvent.click(screen.getByText("Reset demo"));expect(screen.getByLabelText("Current run")).toHaveValue("demo-1");
});
