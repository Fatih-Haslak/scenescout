"use strict";
const $ = (id) => document.getElementById(id);
const translations = {
  en: {
    library: "Your library",
    addVideo: "Add videos",
    sampleEvery: "Sample every",
    allVideos: "All videos",
    local: "Processed on your device",
    privacy: "Your videos stay here. No account. No cloud upload.",
    apiDocs: "Developer API",
    workspace: "Video search workspace",
    headline: "Find the moment.\nKeep the story.",
    subhead: "Describe a scene. Jump straight to it.",
    powered: "Powered by EmbeddingGemma 2",
    searchLabel: "Describe a scene",
    search: "Find scene",
    scopeAll: "Searching across your library",
    shortcut: "Press / to search",
    emptyTitle: "Every great story starts with a scene.",
    emptyText: "Add a video to make its moments searchable.",
    addFirst: "Add your first video",
    formats: "MP4 or WebM · up to 512 MB per video",
    preview: "Preview",
    noSelection: "No video selected",
    copyTime: "Copy timecode",
    filmstrip: "At a glance",
    timelineEmpty: "Your video’s visual timeline",
    stripEmpty: "Indexed frames appear here. Click one to explore.",
    moments: "Matching moments",
    export: "Export",
    resultsHint: "The closest scenes, with timecodes.",
    resultsEmpty: "A scene is worth a thousand keywords.",
    resultsEmptyText: "Try “a wide mountain landscape” or use a reference image.",
    example1: "A rabbit in the grass",
    example2: "A mountain landscape",
    scoreNote: "Results are ranked by visual similarity, not certainty. Audio is not searched.",
    footer: "Built for the scenes you remember, not the filenames you forgot.",
    removeTitle: "Remove this video?",
    removeText:
      "Its imported copy and search index will be deleted. Your original file is untouched.",
    cancel: "Cancel",
    remove: "Remove video",
    placeholder: "A rabbit sitting in the grass…",
    reference: "Search with a reference image",
    loading: "Loading model · first run downloads weights",
    notLoaded: "Model loads on first import",
    modelError: "Model needs attention",
    cpu: "Model ready · CPU",
    cuda: "Model ready · GPU",
    queued: "Waiting to index",
    indexing: "Indexing",
    ready: "Ready",
    error: "Could not index",
    paused: "Paused · frames saved",
    resume: "Resume indexing",
    resuming: "Continuing from saved frames…",
    removing: "Removing",
    frames: "frames",
    uploading: "Importing",
    duplicate: "This video is already in your library.",
    imported: "Video imported. Indexing runs locally; the first import downloads the model.",
    addBefore: "Add a video and wait for indexing to finish, then describe a scene.",
    waitFor: "Wait for this video to finish indexing before searching.",
    emptyQuery: "Describe the scene you want to find.",
    finding: "Finding…",
    noResults: "No indexed scenes yet. Wait for indexing or add a video.",
    matches: "moments",
    searched: "frames searched",
    similarity: "Similarity",
    best: "Top match",
    copied: "Timecode copied.",
    copyFailed: "Your browser could not copy the timecode. Use the time shown on the video.",
    uploadLarge: "Each video must be smaller than 512 MB.",
    uploadFormat: "Choose an MP4 or WebM video.",
    imageLarge: "Reference image must be smaller than 8 MB.",
    network: "Could not connect. Make sure SceneScout is still running.",
    playError:
      "Your browser could not play this video. Convert it to H.264 MP4; indexed scenes can still be searched.",
    imageQuery: "Reference image",
    scope: "Searching in",
    deleteLabel: "Remove",
    saved: "Search results exported.",
    removed: "Video removed from the local library.",
    stale: "Library refreshed. Search again to get current results.",
  },
  tr: {
    library: "Video kitaplığın",
    addVideo: "Video ekle",
    sampleEvery: "Kare aralığı",
    allVideos: "Tüm videolar",
    local: "Cihazında işlenir",
    privacy: "Videolar burada kalır. Hesap gerekmez. Buluta yüklenmez.",
    apiDocs: "Geliştirici API’si",
    workspace: "Video arama alanı",
    headline: "O anı bul.\nHikâyeni tamamla.",
    subhead: "Sahneyi tarif et. Doğrudan o ana git.",
    powered: "EmbeddingGemma 2 ile çalışır",
    searchLabel: "Sahneyi tarif et",
    search: "Sahneyi bul",
    scopeAll: "Tüm kitaplığında aranıyor",
    shortcut: "Aramak için / tuşuna bas",
    emptyTitle: "Her güzel hikâye bir sahneyle başlar.",
    emptyText: "Bir video ekle, içindeki anları aranabilir yap.",
    addFirst: "İlk videonu ekle",
    formats: "MP4 veya WebM · video başına en fazla 512 MB",
    preview: "Önizleme",
    noSelection: "Video seçilmedi",
    copyTime: "Zamanı kopyala",
    filmstrip: "Bir bakışta",
    timelineEmpty: "Videonun görsel zaman çizelgesi",
    stripEmpty: "İndekslenen kareler burada görünür. Keşfetmek için tıkla.",
    moments: "Eşleşen anlar",
    export: "Dışa aktar",
    resultsHint: "Zaman kodlarıyla en yakın sahneler.",
    resultsEmpty: "Sahneyi hatırlaman yeterli.",
    resultsEmptyText: "“Geniş bir dağ manzarası” yaz veya örnek bir görselle ara.",
    example1: "Çimenlerde bir tavşan",
    example2: "Dağ manzarası",
    scoreNote:
      "Sonuçlar görsel benzerliğe göre sıralanır, kesinlik belirtmez. Seste arama yapılmaz.",
    footer: "Dosya adını değil, sahneyi hatırlayanlar için.",
    removeTitle: "Video kaldırılsın mı?",
    removeText: "İçe aktarılan kopya ve arama indeksi silinir. Orijinal dosyan değişmez.",
    cancel: "Vazgeç",
    remove: "Videoyu kaldır",
    placeholder: "Çimenlerde oturan bir tavşan…",
    reference: "Örnek görselle ara",
    loading: "Model hazırlanıyor · ilk açılışta indirilir",
    notLoaded: "Model ilk videoda yüklenir",
    modelError: "Model yüklenemedi",
    cpu: "Model hazır · CPU",
    cuda: "Model hazır · GPU",
    queued: "Sırada bekliyor",
    indexing: "İndeksleniyor",
    ready: "Hazır",
    error: "İndekslenemedi",
    paused: "Duraklatıldı · kareler kaydedildi",
    resume: "İndekslemeye devam et",
    resuming: "Kaydedilen karelerden devam ediliyor…",
    removing: "Kaldırılıyor",
    frames: "kare",
    uploading: "İçe aktarılıyor",
    duplicate: "Bu video zaten kitaplığında.",
    imported: "Video eklendi. Yerelde indeksleniyor; ilk videoda model indirilir.",
    addBefore: "Video ekle ve indekslemenin bitmesini bekle. Sonra sahneyi tarif et.",
    waitFor: "Aramadan önce bu videonun indekslenmesini bekle.",
    emptyQuery: "Bulmak istediğin sahneyi tarif et.",
    finding: "Aranıyor…",
    noResults: "Henüz hazır sahne yok. İndekslemeyi bekle veya video ekle.",
    matches: "an",
    searched: "kare arandı",
    similarity: "Benzerlik",
    best: "İlk eşleşme",
    copied: "Zaman kodu kopyalandı.",
    copyFailed: "Tarayıcı zaman kodunu kopyalayamadı. Videoda görünen zamanı kullan.",
    uploadLarge: "Her video 512 MB’den küçük olmalı.",
    uploadFormat: "MP4 veya WebM video seç.",
    imageLarge: "Örnek görsel 8 MB’den küçük olmalı.",
    network: "Bağlantı kurulamadı. SceneScout’un çalıştığını kontrol et.",
    playError:
      "Tarayıcı bu videoyu oynatamadı. H.264 MP4’e dönüştür; indekslenen sahnelerde aramaya devam edebilirsin.",
    imageQuery: "Örnek görsel",
    scope: "Aranan video",
    deleteLabel: "Kaldır",
    saved: "Arama sonuçları dışa aktarıldı.",
    removed: "Video yerel kitaplıktan kaldırıldı.",
    stale: "Kitaplık yenilendi. Güncel sonuçlar için yeniden ara.",
  },
};
let lang =
  localStorage.getItem("scenescout-language") ||
  (navigator.language.startsWith("tr") ? "tr" : "en");
if (!translations[lang]) lang = "en";
const t = (key) => translations[lang][key] || key;
const state = {
  videos: [],
  scope: null,
  preview: null,
  results: null,
  busy: false,
  selected: null,
  model: null,
  deleting: null,
  queryLabel: "",
  queryType: "text",
  librarySignature: "",
  previewStatus: null,
  searchEpoch: 0,
};
const emptyResults = $("results").firstElementChild.cloneNode(true);
const timecode = (seconds) => {
  const s = Math.max(0, Math.floor(seconds || 0));
  return (
    (s >= 3600
      ? `${Math.floor(s / 3600)
          .toString()
          .padStart(2, "0")}:`
      : "") +
    `${Math.floor(s / 60) % 60}`.padStart(2, "0") +
    ":" +
    `${s % 60}`.padStart(2, "0")
  );
};
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function notice(message, error = false) {
  $("notice").textContent = message;
  $("notice").className = error ? "notice error" : "notice";
  $("notice").hidden = !message;
}
async function api(path, options) {
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error(t("network"));
  }
  if (!response.ok) {
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {}
    throw new Error(
      typeof detail === "string" ? detail : `${response.status} ${response.statusText}`,
    );
  }
  return response.json();
}
function translate() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const text = t(node.dataset.i18n);
    if (node.dataset.i18n === "headline") {
      node.replaceChildren();
      text.split("\n").forEach((line, i) => {
        if (i) node.append(document.createElement("br"));
        node.append(document.createTextNode(line));
      });
    } else node.textContent = text;
  });
  $("query").placeholder = t("placeholder");
  $("reference-button").title = t("reference");
  $("reference-button").setAttribute("aria-label", t("reference"));
  $("language").textContent = lang === "en" ? "Türkçe" : "English";
  renderLibrary();
  renderModel();
  renderResults();
  renderScope();
  const preview = state.videos.find((v) => v.id === state.preview);
  if (preview) $("current-name").textContent = preview.name;
  $("search-button").textContent = t(state.busy ? "finding" : "search");
}
function renderModel() {
  const status = state.model;
  if (!status) return;
  const key =
    status.state === "ready"
      ? status.device
      : status.state === "loading"
        ? "loading"
        : status.state === "error"
          ? "modelError"
          : "notLoaded";
  $("model-status").textContent = t(key);
  $("model-status").className = status.state === "ready" ? "status-pill ready" : "status-pill";
}
function renderScope() {
  const video = state.videos.find((v) => v.id === state.scope);
  $("scope-label").textContent = video ? `${t("scope")}: ${video.name}` : t("scopeAll");
  $("all-videos").classList.toggle("selected", !state.scope);
}
function renderLibrary() {
  const list = $("library-list");
  const focused = document.activeElement?.dataset.libraryKey;
  list.replaceChildren();
  $("video-count").textContent = state.videos.length;
  state.videos.forEach((video) => {
    const row = el("div", "library-item" + (state.scope === video.id ? " selected" : ""));
    const select = el("button", "library-select");
    select.dataset.libraryKey = `${video.id}:select`;
    select.title = video.error || video.name;
    select.append(el("strong", null, video.name));
    const progress = ["indexing", "paused", "error"].includes(video.status)
      ? ` ${video.progress}/${video.total || "…"}`
      : video.status === "ready"
        ? ` · ${timecode(video.duration)} · ${video.progress} ${t("frames")}`
        : "";
    select.append(el("small", null, t(video.status) + progress));
    select.onclick = () => {
      state.scope = video.id;
      renderScope();
      renderLibrary();
      if (video.status === "error") notice(video.error, true);
      else if (video.status === "ready") notice("");
      showVideo(video.id, 0);
    };
    const remove = el("button", "remove-button", "×");
    remove.dataset.libraryKey = `${video.id}:remove`;
    remove.setAttribute("aria-label", `${t("deleteLabel")} ${video.name}`);
    remove.onclick = () => {
      state.deleting = video.id;
      $("remove-dialog").showModal();
    };
    row.append(select);
    const actions = el("div", "library-actions");
    if (["paused", "error"].includes(video.status)) {
      const resume = el("button", "resume-button", "↻");
      resume.dataset.libraryKey = `${video.id}:resume`;
      resume.setAttribute("aria-label", `${t("resume")} ${video.name}`);
      resume.title = t("resume");
      resume.onclick = async () => {
        resume.disabled = true;
        try {
          await api(`/api/videos/${video.id}/resume`, { method: "POST" });
          notice(t("resuming"));
          await refresh();
        } catch (error) {
          notice(error.message, true);
          resume.disabled = false;
        }
      };
      actions.append(resume);
    }
    actions.append(remove);
    row.append(actions);
    list.append(row);
  });
  if (focused) {
    [...list.querySelectorAll("button")]
      .find((button) => button.dataset.libraryKey === focused)
      ?.focus({ preventScroll: true });
  }
}
async function refresh() {
  try {
    const [videos, status] = await Promise.all([api("/api/videos"), api("/api/status")]);
    state.videos = videos;
    state.model = status.model;
    const signature = JSON.stringify(videos);
    if (signature !== state.librarySignature) {
      state.librarySignature = signature;
      renderLibrary();
      renderScope();
      const current = videos.find((v) => v.id === state.preview);
      if (current && current.status !== state.previewStatus) {
        state.previewStatus = current.status;
        await renderFilmstrip(current.id);
      }
      if (state.preview && !current) {
        clearPreview();
      }
      if (state.scope && !videos.some((v) => v.id === state.scope)) state.scope = null;
      renderScope();
    }
    renderModel();
  } catch (error) {
    notice(error.message, true);
  } finally {
    setTimeout(refresh, 1800);
  }
}
function clearPreview() {
  state.preview = null;
  state.previewStatus = null;
  $("player").pause();
  $("player").removeAttribute("src");
  $("player").load();
  $("player").hidden = true;
  $("empty-viewer").hidden = false;
  $("viewer-badge").hidden = true;
  $("current-name").textContent = t("noSelection");
  $("copy-time").disabled = true;
  $("filmstrip").replaceChildren(el("div", "empty-strip", t("stripEmpty")));
  $("timeline-info").textContent = t("timelineEmpty");
}
async function showVideo(videoId, timestamp) {
  const item = state.videos.find((v) => v.id === videoId);
  if (!item) return;
  const player = $("player");
  if (state.preview !== videoId) {
    state.preview = videoId;
    state.previewStatus = item.status;
    player.pause();
    player.src = `/api/videos/${videoId}/media`;
    player.hidden = false;
    $("empty-viewer").hidden = true;
    $("current-name").textContent = item.name;
    player.onloadedmetadata = () => {
      player.currentTime = Math.min(timestamp, player.duration || timestamp);
    };
    await renderFilmstrip(videoId);
  } else if (player.readyState >= 1) {
    player.currentTime = Math.min(timestamp, player.duration || timestamp);
  } else
    player.onloadedmetadata = () => {
      player.currentTime = timestamp;
    };
  $("viewer-badge").hidden = false;
  $("viewer-badge").textContent = timecode(timestamp);
  $("copy-time").disabled = false;
}
async function renderFilmstrip(videoId) {
  try {
    const scenes = await api(`/api/videos/${videoId}/scenes`);
    if (state.preview !== videoId) return;
    const strip = $("filmstrip");
    strip.replaceChildren();
    if (!scenes.length) {
      strip.append(el("div", "empty-strip", t("stripEmpty")));
      return;
    }
    const video = state.videos.find((v) => v.id === videoId);
    $("timeline-info").textContent =
      `${video.progress} ${t("frames")} · ${timecode(video.duration)}`;
    scenes.forEach((scene) => {
      const button = el("button", "strip-frame");
      button.setAttribute("aria-label", `${timecode(scene.timestamp)}`);
      button.dataset.timestamp = scene.timestamp;
      const image = el("img");
      image.src = scene.thumbnail;
      image.alt = "";
      image.loading = "lazy";
      button.append(image, el("span", null, timecode(scene.timestamp)));
      button.onclick = () => {
        showVideo(videoId, scene.timestamp);
      };
      strip.append(button);
    });
  } catch (error) {
    notice(error.message, true);
  }
}
function renderResults() {
  const results = $("results");
  results.replaceChildren();
  if (!state.results) {
    results.append(emptyResults.cloneNode(true));
    results
      .querySelectorAll("[data-i18n]")
      .forEach((node) => (node.textContent = t(node.dataset.i18n)));
    $("result-summary").textContent = t("resultsHint");
    $("export-results").disabled = true;
    return;
  }
  const response = state.results;
  $("result-summary").textContent =
    `${state.queryType === "image" ? t("imageQuery") + " · " : ""}${response.results.length} ${t("matches")} · ${response.elapsed_ms} ms · ${response.searched_frames} ${t("searched")}`;
  $("export-results").disabled = !response.results.length;
  if (!response.results.length) {
    results.append(el("p", "result-summary", t("noResults")));
    return;
  }
  response.results.forEach((scene, i) => {
    const row = el("button", "result" + (state.selected === scene.id ? " selected" : ""));
    row.setAttribute(
      "aria-label",
      `${scene.name}, ${timecode(scene.timestamp)}, ${t("similarity")} ${scene.score}`,
    );
    const image = el("img", "result-image");
    image.src = scene.thumbnail;
    image.alt = "";
    image.loading = "lazy";
    const details = el("div", "result-details");
    const stamp = el("div", "result-time", timecode(scene.timestamp));
    if (i === 0) stamp.append(el("span", "result-rank", t("best")));
    details.append(
      stamp,
      el("div", "result-name", scene.name),
      el("div", "result-score", `${t("similarity")} ${scene.score.toFixed(3)}`),
    );
    row.append(image, details);
    row.onclick = () => {
      state.selected = scene.id;
      renderResults();
      showVideo(scene.video_id, scene.timestamp);
    };
    results.append(row);
  });
}
async function search(image) {
  if (state.busy) return;
  if (!state.videos.some((v) => v.status === "ready")) {
    notice(t("addBefore"));
    return;
  }
  if (state.scope && state.videos.find((v) => v.id === state.scope)?.status !== "ready") {
    notice(t("waitFor"));
    return;
  }
  const query = $("query").value.trim();
  if (!image && !query) {
    notice(t("emptyQuery"));
    $("query").focus();
    return;
  }
  if (image && image.size > 8 * 1024 * 1024) {
    notice(t("imageLarge"), true);
    return;
  }
  state.busy = true;
  const epoch = state.searchEpoch;
  $("search-button").disabled = true;
  $("reference-button").disabled = true;
  $("search-button").textContent = t("finding");
  notice("");
  try {
    let response;
    if (image) {
      const form = new FormData();
      form.append("file", image);
      if (state.scope) form.append("video_id", state.scope);
      response = await api("/api/search/image", { method: "POST", body: form });
      state.queryLabel = t("imageQuery");
      state.queryType = "image";
      $("query").value = "";
    } else {
      response = await api("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, video_id: state.scope }),
      });
      state.queryLabel = query;
      state.queryType = "text";
    }
    if (epoch !== state.searchEpoch) return;
    state.results = response;
    state.selected = response.results[0]?.id || null;
    renderResults();
    if (response.results.length)
      await showVideo(response.results[0].video_id, response.results[0].timestamp);
  } catch (error) {
    notice(error.message, true);
  } finally {
    state.busy = false;
    $("search-button").disabled = false;
    $("reference-button").disabled = false;
    $("search-button").textContent = t("search");
  }
}
function upload(file) {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append("file", file);
    form.append("interval", $("interval").value);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/videos");
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable)
        notice(
          `${t("uploading")} ${file.name} · ${Math.round((event.loaded / event.total) * 100)}%`,
        );
    };
    xhr.onerror = () => reject(new Error(t("network")));
    xhr.onload = () => {
      let body;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {}
      if (xhr.status >= 200 && xhr.status < 300) resolve(body);
      else
        reject(
          new Error(
            typeof body?.detail === "string" ? body.detail : `${xhr.status} ${xhr.statusText}`,
          ),
        );
    };
    xhr.send(form);
  });
}
$("video-input").onchange = async () => {
  const files = [...$("video-input").files];
  document.body.classList.add("uploading");
  $("import-button").disabled = true;
  try {
    for (const file of files) {
      if (file.size > 512 * 1024 * 1024) throw new Error(t("uploadLarge"));
      if (!/\.(mp4|webm)$/i.test(file.name)) throw new Error(t("uploadFormat"));
      const result = await upload(file);
      notice(t(result.duplicate ? "duplicate" : "imported"));
      state.videos = await api("/api/videos");
      renderLibrary();
      await showVideo(result.id, 0);
    }
  } catch (error) {
    notice(error.message, true);
  } finally {
    $("video-input").value = "";
    document.body.classList.remove("uploading");
    $("import-button").disabled = false;
  }
};
$("import-button").onclick = () => $("video-input").click();
$("empty-import").onclick = () => $("video-input").click();
$("reference-button").onclick = () => $("reference-input").click();
$("reference-input").onchange = () => {
  const file = $("reference-input").files[0];
  if (file) search(file);
  $("reference-input").value = "";
};
$("search-form").onsubmit = (event) => {
  event.preventDefault();
  search();
};
$("all-videos").onclick = () => {
  state.scope = null;
  renderLibrary();
  renderScope();
};
$("language").onclick = () => {
  lang = lang === "en" ? "tr" : "en";
  localStorage.setItem("scenescout-language", lang);
  translate();
  if (state.preview) renderFilmstrip(state.preview);
};
$("results").addEventListener("click", (event) => {
  const example = event.target.closest("[data-example]");
  if (example) {
    $("query").value =
      lang === "tr"
        ? example.dataset.i18n === "example1"
          ? "Çimenlerde oturan bir tavşan"
          : "Geniş bir dağ manzarası"
        : example.dataset.example;
    search();
  }
});
$("player").ontimeupdate = () => {
  $("viewer-badge").textContent = timecode($("player").currentTime);
  const frames = [...$("filmstrip").children].filter(
    (node) => node.dataset.timestamp !== undefined,
  );
  const current = $("player").currentTime;
  let nearest = frames[0];
  for (const node of frames) {
    if (Number(node.dataset.timestamp) <= current) nearest = node;
  }
  frames.forEach((node) => node.classList.toggle("active", node === nearest));
};
$("player").onerror = () => {
  if (state.preview) notice(t("playError"), true);
};
$("copy-time").onclick = async () => {
  try {
    const video = state.videos.find((v) => v.id === state.preview);
    await navigator.clipboard.writeText(`${video.name} @ ${timecode($("player").currentTime)}`);
    notice(t("copied"));
  } catch {
    notice(t("copyFailed"), true);
  }
};
$("export-results").onclick = () => {
  const data = {
    query: state.queryLabel,
    query_type: state.queryType,
    model: "google/embeddinggemma-2",
    exported_at: new Date().toISOString(),
    ...state.results,
  };
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  const link = el("a");
  link.href = url;
  link.download = "scenescout-results.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  notice(t("saved"));
};
$("remove-dialog").onclose = async () => {
  if ($("remove-dialog").returnValue !== "confirm" || !state.deleting) return;
  try {
    state.searchEpoch += 1;
    await api(`/api/videos/${state.deleting}`, { method: "DELETE" });
    if (state.preview === state.deleting) clearPreview();
    if (state.scope === state.deleting) state.scope = null;
    state.results = null;
    renderResults();
    notice(t("removed"));
  } catch (error) {
    notice(error.message, true);
  } finally {
    state.deleting = null;
  }
};
document.addEventListener("keydown", (event) => {
  if (
    event.key === "/" &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.altKey &&
    !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) &&
    !$("remove-dialog").open
  ) {
    event.preventDefault();
    $("query").focus();
  }
});
translate();
refresh();
