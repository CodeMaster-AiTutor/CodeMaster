import { test, expect } from "@playwright/test";

const editorSelector = ".monaco-editor";
const inputSelector = ".monaco-editor textarea.inputarea";
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
  const input = page.locator(inputSelector);
  await input.click();
  await page.keyboard.type("public class Main { }");
  const value = await page.evaluate(() => {
    const win = window as unknown as {
      monaco?: { editor?: { getModels?: () => Array<{ getValue?: () => string }> } };
    };
    return win.monaco?.editor?.getModels?.()[0]?.getValue?.() ?? "";
  });
  expect(value).toContain("public class Main { }");
  await expect(input).toBeFocused();
});

test("keeps cursor focused until blur", async ({ page }) => {
  await page.goto("/compiler");
  await page.waitForSelector(editorSelector);
  const input = page.locator(inputSelector);
  await input.click();
  await page.keyboard.type("class A {}");
  await expect(input).toBeFocused();
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
  const input = page.locator(inputSelector);
  await input.click();
  await page.keyboard.type("\nLine 121");
  const currentScroll = await page.evaluate(
    (scrollSelector) => (document.querySelector(scrollSelector) as HTMLElement | null)?.scrollTop ?? 0,
    scrollSelector,
  );
  expect(currentScroll).toBeGreaterThanOrEqual(240);
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
  const input = page.locator(inputSelector);
  await input.click();
  await page.keyboard.type("\nRow 161");
  const currentScroll = await page.evaluate(
    (scrollSelector) => (document.querySelector(scrollSelector) as HTMLElement | null)?.scrollTop ?? 0,
    scrollSelector,
  );
  expect(currentScroll).toBeGreaterThan(0);
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
  const input = page.locator(inputSelector);
  await input.click();
  await page.keyboard.press("End");
  await page.keyboard.type("\n\n\n\n");
  const scrollTop = await page.evaluate(
    (scrollSelector) => (document.querySelector(scrollSelector) as HTMLElement | null)?.scrollTop ?? 0,
    scrollSelector,
  );
  expect(scrollTop).toBeGreaterThan(0);
});
