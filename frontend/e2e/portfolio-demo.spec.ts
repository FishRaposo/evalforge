import { expect, test } from "@playwright/test";
for (const width of [390,768,1440]) {
 test(`offline sample journey, reset and keyboard at ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:width===390?844:width===768?1024:900});await page.emulateMedia({reducedMotion:"reduce"});
  const requests:string[]=[];const errors:string[]=[];
  page.on("console",message=>{if(message.type()==="error")errors.push(message.text());});
  page.on("request",r=>{if(!new URL(r.url()).host.includes("127.0.0.1:3002"))requests.push(r.url());});
  page.on("pageerror",e=>errors.push(e.message));
  await page.goto("/");
  await expect(page.getByRole("heading",{level:1})).toHaveText("Catch the AI answers that look right and cite the wrong evidence.");
  await expect(page.getByTestId("demo-banner")).toContainText("Interactive sample data");
  await page.screenshot({path:`../.tmp/sample-overview-${width}.png`,animations:"disabled"});
  await page.getByRole("button",{name:"Start guided demo"}).click();
  await page.getByRole("button",{name:"Introduce wrong source",exact:true}).click();
  await expect(page.getByTestId("release-gate")).toContainText("Release blocked");
  await expect(page.getByTestId("case-ef-answerable-002")).toContainText("Aster trial policy");
  await page.getByTestId("case-ef-answerable-002").evaluate(element=>element.scrollIntoView({block:"start"}));
  await page.screenshot({path:`../.tmp/sample-evidence-${width}.png`,animations:"disabled"});
  await page.getByRole("button",{name:"Why did it fail?"}).click();
  await page.getByRole("button",{name:"Compare repaired candidate"}).click();
  await expect(page.getByTestId("release-gate")).toContainText("Contract passed");
  await page.getByRole("button",{name:"Open judge-error case"}).click();
  await expect(page.getByTestId("release-gate")).toContainText("Cannot evaluate");
  await page.getByRole("button",{name:"Retry fixture",exact:true}).first().click();
  await expect(page.getByTestId("release-gate")).toContainText("Contract passed");
  await page.getByRole("button",{name:"Reset demo"}).click();
  await expect(page.getByTestId("case-ef-answerable-001")).toBeVisible();
  await expect(page.getByRole("button",{name:/Correct citation/})).toHaveAttribute("aria-pressed","true");
  const caseButton=page.getByRole("button",{name:/Wrong source, similar wording/});await caseButton.focus();await page.keyboard.press("Enter");
  await expect(caseButton).toHaveAttribute("aria-pressed","true");
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  for (const route of ["/compare", "/evaluate", "/runs/demo-7", "/runs/demo-repaired"]) {
   await page.goto(route);
   await expect(page.locator("main")).toContainText(route==="/evaluate"?"Connect to run your evaluator":route==="/compare"?"Compare releases":"six-case preview");
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   if(route==="/runs/demo-7"){
    await expect(page.getByRole("complementary",{name:"Test cases"}).getByRole("button").first().locator("span").nth(1)).toBeVisible();
   }
  }
  expect(errors).toEqual([]);expect(requests).toEqual([]);
 });
}
test("mode preference survives navigation/reload and connected outage requires explicit sample entry",async({page})=>{
 await page.route("http://127.0.0.1:8200/**",r=>r.abort());await page.goto("/");
 await page.getByLabel("Data source").selectOption("connected");await expect(page.getByRole("heading",{name:"Connected API unavailable"})).toBeVisible();
 await expect(page.getByTestId("demo-banner")).toHaveCount(0);await page.reload();await expect(page.getByLabel("Data source")).toHaveValue("connected");
 await page.getByRole("button",{name:"Enter sample mode"}).click();await expect(page.getByTestId("demo-banner")).toBeVisible();
 await page.getByRole("link",{name:"Compare",exact:true}).click();await expect(page.getByLabel("Data source")).toHaveValue("sample");
 await expect(page.getByText("Candidate answer & evidence")).toBeVisible();
});
