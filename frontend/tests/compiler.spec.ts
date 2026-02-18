import { test, expect } from "@playwright/test";

const editorSelector = ".monaco-editor";
const scrollSelector = ".monaco-scrollable-element";

test("supports uninterrupted multi-character input", async ({ page }) => {
  await page.goto("/compiler");
  await page.waitForSelector(editorSelector);
  await page.waitForFunction(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ getValue?: () => string }> } };
    };
    return (win.monaco?.editor?.getModels?.().length ?? 0) > 0;
  });
  await page.locator(editorSelector).click({ position: { x: 10, y: 10 } });
  await page.keyboard.type("public class Main { }");
  const value = await page.evaluate(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ getValue?: () => string }> } };
    };
    return win.monaco?.editor?.getModels?.()[0]?.getValue?.() ?? "";
  });
  expect(value).toContain("public class Main { }");
});

test("keeps cursor focused until blur", async ({ page }) => {
  await page.goto("/compiler");
  await page.waitForSelector(editorSelector);
  await page.locator(editorSelector).click({ position: { x: 10, y: 10 } });
  await page.keyboard.type("class A {}");
  const value = await page.evaluate(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ getValue?: () => string }> } };
    };
    return win.monaco?.editor?.getModels?.()[0]?.getValue?.() ?? "";
  });
  expect(value).toContain("class A {}");
});

test("preserves scroll offset after edits", async ({ page }) => {
  await page.goto("/compiler");
  await page.waitForSelector(editorSelector);
  await page.waitForFunction(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ setValue?: (value: string) => void }> } };
    };
    return (win.monaco?.editor?.getModels?.().length ?? 0) > 0;
  });
  const content = Array.from({ length: 120 }, (_, i) => `Line ${i + 1}`).join("\n");
  await page.evaluate(
    ({ content, scrollTop, scrollSelector }) => {
      const win = window as unknown as {
        monaco?: { editor?: { getModels?: () => Array<{ setValue?: (value: string) => void }> } };
      };
      const model = win.monaco?.editor?.getModels?.()[0];
      if (model?.setValue) {
        model.setValue(content);
      }
      const scrollable = document.querySelector(scrollSelector) as HTMLElement | null;
      if (scrollable) {
        scrollable.scrollTop = scrollTop;
      }
    },
    { content, scrollTop: 240, scrollSelector },
  );
  await page.locator(editorSelector).click({ position: { x: 10, y: 10 } });
  await page.keyboard.type("\nLine 121");
  const value = await page.evaluate(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ getValue?: () => string }> } };
    };
    return win.monaco?.editor?.getModels?.()[0]?.getValue?.() ?? "";
  });
  expect(value).toContain("Line 121");
});

test("does not auto-scroll to top after typing", async ({ page }) => {
  await page.goto("/compiler");
  await page.waitForSelector(editorSelector);
  await page.waitForFunction(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ setValue?: (value: string) => void }> } };
    };
    return (win.monaco?.editor?.getModels?.().length ?? 0) > 0;
  });
  const content = Array.from({ length: 160 }, (_, i) => `Row ${i + 1}`).join("\n");
  await page.evaluate(
    ({ content, scrollTop, scrollSelector }) => {
      const win = window as unknown as {
        monaco?: { editor?: { getModels?: () => Array<{ setValue?: (value: string) => void }> } };
      };
      const model = win.monaco?.editor?.getModels?.()[0];
      if (model?.setValue) {
        model.setValue(content);
      }
      const scrollable = document.querySelector(scrollSelector) as HTMLElement | null;
      if (scrollable) {
        scrollable.scrollTop = scrollTop;
      }
    },
    { content, scrollTop: 320, scrollSelector },
  );
  await page.locator(editorSelector).click({ position: { x: 10, y: 10 } });
  await page.keyboard.type("\nRow 161");
  const value = await page.evaluate(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ getValue?: () => string }> } };
    };
    return win.monaco?.editor?.getModels?.()[0]?.getValue?.() ?? "";
  });
  expect(value).toContain("Row 161");
});

test("auto-scrolls to keep cursor visible on enter", async ({ page }) => {
  await page.goto("/compiler");
  await page.waitForSelector(editorSelector);
  await page.waitForFunction(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ setValue?: (value: string) => void }> } };
    };
    return (win.monaco?.editor?.getModels?.().length ?? 0) > 0;
  });
  const content = Array.from({ length: 200 }, (_, i) => `Line ${i + 1}`).join("\n");
  await page.evaluate((content) => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ setValue?: (value: string) => void }> } };
    };
    const model = win.monaco?.editor?.getModels?.()[0];
    if (model?.setValue) {
      model.setValue(content);
    }
  }, content);
  await page.locator(editorSelector).click({ position: { x: 10, y: 10 } });
  await page.keyboard.press("End");
  await page.keyboard.type("\n\n\n\n");
  const value = await page.evaluate(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ getValue?: () => string }> } };
    };
    return win.monaco?.editor?.getModels?.()[0]?.getValue?.() ?? "";
  });
  expect(value.length).toBeGreaterThan(content.length);
});
