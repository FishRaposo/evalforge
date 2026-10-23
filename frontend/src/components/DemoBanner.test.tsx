import {render,screen} from "@testing-library/react";
import {describe,expect,it} from "vitest";
import {DemoBanner} from "./DemoBanner";
describe("DemoBanner",()=>{
 it("labels snapshots and synthetic provenance without suggesting automatic fallback",()=>{render(<DemoBanner/>);expect(screen.getByText("Interactive sample data")).toBeInTheDocument();expect(screen.getByText(/agent-authored labels/)).toBeInTheDocument();expect(screen.getByText(/no model is running/)).toBeInTheDocument();expect(screen.queryByText(/API is not reachable/)).not.toBeInTheDocument();});
 it("retains an explicit accessibility status",()=>{render(<DemoBanner/>);expect(screen.getByRole("status")).toBeInTheDocument();});
});
