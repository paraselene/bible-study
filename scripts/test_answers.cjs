// Isolated JavaScript checks; no browser or network access is used.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const code = fs.readFileSync(path.join(__dirname, "../study/static/study/site.js"), "utf8");
const labels = {saved: "Saved", saving: "Saving", save_error: "Save failed", cleared: "Cleared"};

function storage() {
  const result = {};
  let blocked = false;
  Object.defineProperties(result, {
    getItem: {value(key) { if (blocked) throw Error("Blocked"); return result[key] ?? null; }},
    setItem: {value(key, value) { if (blocked) throw Error("Blocked"); result[key] = String(value); }},
    removeItem: {value(key) { if (blocked) throw Error("Blocked"); delete result[key]; }},
    block: {value() { blocked = true; }},
  });
  return result;
}

function element(extra = {}) {
  return {
    value: "", listeners: {}, textContent: "", failed: false,
    addEventListener(name, callback) { this.listeners[name] = callback; },
    ...extra,
  };
}

function mount(store, options = {}) {
  const lessonId = options.lessonId || "u23-s1";
  const inputs = (options.questions || ["discussion-1", "wrap-up"]).map(id => element({dataset: {question: id}}));
  const status = element();
  status.classList = {toggle(name, enabled) { status.failed = enabled; }};
  const clear = element();
  const dialog = element({open: false, returnValue: "", showModal() { this.open = true; }});
  const language = element({submitted: 0});
  language.form = {requestSubmit() { language.submitted++; }};
  const ids = {"save-status": status, "clear-answers": clear, "clear-dialog": dialog, "study-labels": {textContent: JSON.stringify(options.labels || labels)}};
  const window = element({reloads: 0});
  window.location = {reload() { window.reloads++; }};
  const document = {
    querySelector() { return {dataset: {lesson: lessonId}}; },
    querySelectorAll(selector) { return selector === "[data-auto-submit]" ? [language] : inputs; },
    getElementById(id) { return ids[id]; },
  };
  vm.runInNewContext(code, {document, window, localStorage: store});
  return {inputs, status, clear, dialog, language, window};
}

const store = storage();
let page = mount(store);
const answer = "我的回應保持原樣：繁體中文、简体字、English 🌿\n第二行";
page.inputs[0].value = answer;
page.inputs[0].listeners.input();
assert.equal(page.status.textContent, "Saved");
assert.equal(store.getItem("biblestudy.answers.v1:u23-s1:discussion-1"), answer);

page = mount(store); // Reload.
assert.equal(page.inputs[0].value, answer);
page = mount(store, {labels: {...labels, saved: "已保存"}}); // Language switch.
assert.equal(page.inputs[0].value, answer);
page = mount(store, {questions: ["discussion-1", "activity-1", "wrap-up"]}); // Guide switch.
assert.equal(page.inputs[0].value, answer);
store.setItem("biblestudy.answers.v1:u23-s1:activity-2", "hidden guide answer");
store.setItem("biblestudy.answers.v1:u23-s2:discussion-1", "other lesson");
store.setItem("unrelated", "keep");

page.clear.listeners.click();
assert.equal(page.dialog.open, true);
page.dialog.returnValue = "cancel";
page.dialog.listeners.close();
assert.equal(page.inputs[0].value, answer);
page.dialog.returnValue = "clear";
page.dialog.listeners.close();
assert.equal(page.inputs[0].value, "");
assert.equal(store.getItem("biblestudy.answers.v1:u23-s1:activity-2"), null);
assert.equal(store.getItem("biblestudy.answers.v1:u23-s2:discussion-1"), "other lesson");
assert.equal(store.getItem("unrelated"), "keep");
assert.equal(page.status.textContent, "Cleared");

page.language.listeners.change();
assert.equal(page.language.submitted, 1);
page.window.listeners.pageshow({persisted: false});
assert.equal(page.window.reloads, 0);
page.window.listeners.pageshow({persisted: true});
assert.equal(page.window.reloads, 1);

store.block();
page = mount(store);
assert.equal(page.status.textContent, "Save failed");
page.inputs[0].value = answer;
page.inputs[0].listeners.input();
assert.equal(page.inputs[0].value, answer);
assert.equal(page.status.failed, true);
console.log("Answer-storage checks passed: save, reload, language/guide switches, confirmed clearing, storage errors, and restored-page revalidation.");
