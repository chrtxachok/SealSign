"use strict";

const element = (id) => document.getElementById(id);
const picker = element("file");
const dropzone = element("dropzone");
const analyze = element("analyze");
const preview = element("preview");
const overlay = element("overlay");
const status = element("status");
const labels = {stamp: "Печать", signature: "Подпись"};
const percentage = new Intl.NumberFormat("ru", {style: "percent", maximumFractionDigits: 0});
const svgNamespace = "http://www.w3.org/2000/svg";
let file = null;
let result = null;
let busy = false;
let previewUrl = null;

function setStatus(message, isError = false) {
  status.textContent = message;
  status.classList.toggle("error", isError);
}

function clearResult() {
  result = null;
  overlay.replaceChildren();
  element("detections").replaceChildren();
  for (const id of ["detections", "download", "model"]) element(id).hidden = true;
  for (const id of ["count-stamp", "count-signature"]) element(id).textContent = "—";
}

function selectFile(candidate) {
  if (!candidate || busy) return;
  clearResult();
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  preview.removeAttribute("src");
  element("paper").hidden = true;
  dropzone.hidden = false;
  file = candidate;
  element("filename").textContent = file.name;
  element("actions").hidden = false;
  const validSize = file.size > 0 && file.size <= 20 * 1024 * 1024;
  analyze.hidden = !validSize;
  setStatus(validSize ? "Страница готова к анализу." : "Выберите непустой файл до 20 МиБ.", !validSize);
  if (validSize && ["image/jpeg", "image/png"].includes(file.type)) {
    previewUrl = URL.createObjectURL(file);
    const url = previewUrl;
    preview.src = url;
    preview.decode().then(() => {
      if (preview.src !== url) return;
      element("paper").hidden = false;
      dropzone.hidden = true;
    }).catch(() => {});
  }
}

function render(prediction) {
  const {width, height} = prediction.image;
  overlay.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const counts = {stamp: 0, signature: 0};
  const list = element("detections");
  for (const detection of prediction.detections) {
    const {label, confidence} = detection;
    const [x, y, right, bottom] = detection.bbox_xyxy;
    const rect = document.createElementNS(svgNamespace, "rect");
    rect.setAttribute("class", label);
    rect.setAttribute("x", x);
    rect.setAttribute("y", y);
    rect.setAttribute("width", right - x);
    rect.setAttribute("height", bottom - y);
    overlay.append(rect);
    counts[label]++;
    const item = document.createElement("li");
    item.textContent = `${labels[label]} · ${percentage.format(confidence)}`;
    list.append(item);
  }
  for (const name of Object.keys(counts)) element(`count-${name}`).textContent = counts[name];
  list.hidden = !prediction.detections.length;
  element("model").textContent = prediction.model_version;
  element("model").hidden = false;
  element("download").hidden = false;
  element("paper").hidden = false;
  dropzone.hidden = true;
  setStatus(prediction.detections.length ? "Анализ завершён." : "Печати и подписи не найдены.");
}

for (const id of ["choose", "replace"]) element(id).addEventListener("click", () => picker.click());
element("sample").addEventListener("click", async () => {
  if (busy) return;
  const previousFile = file;
  try {
    const response = await fetch("/sample.png");
    if (!response.ok) throw new Error("Sample unavailable");
    const example = await response.blob();
    if (file === previousFile) selectFile(new File([example], "Пример SealSign.png", {type: example.type}));
  } catch {
    if (file === previousFile) setStatus("Не удалось открыть пример.", true);
  }
});
picker.addEventListener("change", () => {
  selectFile(picker.files[0]);
  picker.value = "";
});
for (const event of ["dragover", "dragleave", "drop"]) {
  dropzone.addEventListener(event, (e) => {
    e.preventDefault();
    dropzone.classList.toggle("dragging", event === "dragover" && !busy);
    if (event === "drop") selectFile(e.dataTransfer.files[0]);
  });
}

analyze.addEventListener("click", async () => {
  if (!file || busy) return;
  busy = true;
  clearResult();
  for (const id of ["analyze", "choose", "replace", "sample"]) element(id).disabled = true;
  setStatus("Идёт анализ страницы…");
  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/octet-stream"},
      body: file,
    });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.error, true);
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = null;
    preview.src = `data:image/png;base64,${data.preview_png}`;
    await preview.decode();
    render(data.prediction);
    result = data.prediction;
  } catch {
    setStatus("Анализ недоступен. Проверьте, запущен ли SealSign.", true);
  } finally {
    busy = false;
    for (const id of ["analyze", "choose", "replace", "sample"]) element(id).disabled = false;
  }
});

element("download").addEventListener("click", () => {
  if (!result) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], {type: "application/json"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "sealsign-result.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
