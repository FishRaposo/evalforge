import {expect,test} from "@playwright/test";
test("sample overview has explicit provenance and saved six-case snapshots",async({page})=>{await page.goto("/");await expect(page.getByTestId("demo-banner")).toContainText("Interactive sample data");await page.getByRole("button",{name:"Candidate",exact:true}).click();await expect(page.getByTestId("release-gate")).toContainText("Release blocked");});
