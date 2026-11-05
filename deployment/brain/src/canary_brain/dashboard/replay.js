"use strict";
const $ = (id) => document.getElementById(id),
	state = {
		runs: [],
		chosen: new Map(),
		time: 0,
		playing: false,
		end: 1,
		last: 0,
		request: 0,
	};
const colors = ["#b9e894", "#7ccbd8", "#e8bb7f", "#c4a8ec"],
	labels = {
		sample: "Estado",
		decision: "Decisão",
		proposal: "Proposta",
		intent: "Ação enviada",
		outcome: "Resultado do servidor",
		request: "Chamada ao modelo",
		operator: "Supervisão",
		lifecycle: "Ciclo de vida",
		gap: "Lacuna de observação",
		segment: "Sessão",
		level: "Nível ganho",
		configuration: "Configuração",
	};
const fmt = (n, d = 0) =>
	n === null || n === undefined
		? "indisponível"
		: Number(n).toLocaleString("pt-BR", { maximumFractionDigits: d });
function clock(ms) {
	let s = Math.max(0, Math.floor(ms / 1000));
	return `${Math.floor(s / 3600) ? String(Math.floor(s / 3600)).padStart(2, "0") + ":" : ""}${String(Math.floor(s / 60) % 60).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}
async function api(path, params = {}) {
	const query = new URLSearchParams(params),
		archive = window.REPLAY_ARCHIVE;
	if (archive) {
		const run = archive.runs.find((r) => r.id === params.run);
		if (path === "replays") return archive.runs;
		if (!run) throw Error("Gravação ausente no arquivo");
		const events = archive.events[run.id];
		if (path === "replay") return run;
		if (path.endsWith("/summary")) return archive.summaries[run.id];
		if (path.endsWith("/track"))
			return events.filter((e) => e.kind === "sample");
		if (path.endsWith("/timeline"))
			return events
				.filter((e) => e.kind !== "sample" && e.t_ms <= +params.at)
				.slice(-100)
				.reverse();
		if (path.endsWith("/seek"))
			return {
				sample:
					events
						.filter((e) => e.kind === "sample" && e.t_ms <= +params.at)
						.at(-1) || null,
			};
		throw Error("Consulta indisponível no arquivo");
	}
	const r = await fetch(`/api/${path}?${query}`);
	const value = await r.json();
	if (!r.ok) throw Error(value.error || "Falha ao ler a gravação");
	return value.data;
}
function say(text) {
	$("notice").textContent = text;
}
function offset(run) {
	return $("alignment").value === "level"
		? run.summary.metrics.levels[0]?.t_ms || 0
		: 0;
}
function timeFor(run) {
	return Math.min(run.meta.duration_ms, Math.max(0, state.time + offset(run)));
}
async function select(meta, checked) {
	if (!checked) {
		state.chosen.delete(meta.id);
		layout();
		return;
	}
	if (state.chosen.size >= 4) {
		say("Escolha até quatro jornadas por comparação.");
		renderChoices();
		return;
	}
	const run = {
		meta,
		track: [],
		summary: null,
		node: null,
		sample: null,
		sequence: 0,
	};
	state.chosen.set(meta.id, run);
	try {
		[run.meta, run.track, run.summary] = await Promise.all([
			api("replay", { run: meta.id }),
			api("replay/track", { run: meta.id }),
			api("replay/summary", { run: meta.id }),
		]);
		if (!state.chosen.has(meta.id)) return;
		layout();
		await inspect();
	} catch (e) {
		state.chosen.delete(meta.id);
		say(e.message);
		renderChoices();
	}
}
function renderChoices() {
	const target = $("runs");
	target.replaceChildren();
	for (const r of state.runs) {
		const label = document.createElement("label");
		label.className = "run-choice";
		const box = document.createElement("input");
		box.type = "checkbox";
		box.checked = state.chosen.has(r.id);
		box.addEventListener("change", () => select(r, box.checked));
		const text = document.createElement("span");
		text.textContent = r.manifest.participant;
		const small = document.createElement("small");
		small.textContent = `${r.manifest.model} · ${r.manifest.synthetic ? "SIMULAÇÃO · " : ""}${r.status} · ${r.id}`;
		text.append(small);
		label.append(box, text);
		target.append(label);
	}
}
function metric(parent, title, value) {
	const node = document.createElement("div");
	node.className = "stat";
	const name = document.createElement("span");
	name.textContent = title;
	const strong = document.createElement("strong");
	strong.textContent = value;
	node.append(name, strong);
	parent.append(node);
}
function layout() {
	const arena = $("arena");
	arena.replaceChildren();
	let i = 0;
	for (const r of state.chosen.values()) {
		if (!r.summary) continue;
		r.color = colors[i++];
		const node = $("card").content.firstElementChild.cloneNode(true);
		r.node = node;
		node.querySelector(".participant").textContent =
			r.meta.manifest.participant;
		node.querySelector(".name").textContent =
			`Bot ${r.meta.manifest.bot_id} · ${r.meta.manifest.model}`;
		node.querySelector(".status").textContent = r.meta.manifest.synthetic
			? "simulação"
			: r.meta.status;
		node.querySelector(".provenance").textContent =
			`${r.meta.manifest.scenario} · memória ${r.meta.manifest.memory_mode} · ${r.meta.manifest.provider}`;
		node.querySelector(".manifest").textContent = JSON.stringify(
			{
				manifest: r.meta.manifest,
				incomplete: r.meta.incomplete,
				limitations: r.summary.metrics.limitations,
			},
			null,
			2,
		);
		const m = r.summary.metrics,
			p = node.querySelector(".stats");
		metric(p, "XP líquido da run", fmt(m.xp_delta));
		metric(p, "Mortes confirmadas", fmt(m.deaths));
		metric(p, "Ajuda humana", fmt(m.interventions));
		metric(
			p,
			"Custo liquidado",
			m.spent_nanousd === null
				? "indisponível"
				: `US$ ${fmt(m.spent_nanousd / 1e9, 6)}`,
		);
		metric(
			p,
			"Reserva pendente",
			m.reserved_nanousd === null
				? "indisponível"
				: `US$ ${fmt(m.reserved_nanousd / 1e9, 6)}`,
		);
		metric(p, "XP / hora ativa", fmt(m.xp_per_active_hour, 1));
		for (const h of m.milestones.slice(0, 30)) {
			const b = document.createElement("button");
			b.textContent = `${clock(h.t_ms)} · ${h.text}`;
			b.addEventListener("click", () => jump(Math.max(0, h.t_ms - offset(r))));
			node.querySelector(".highlights").append(b);
		}
		arena.append(node);
	}
	state.end = Math.max(
		1,
		...[...state.chosen.values()]
			.filter((r) => r.summary)
			.map((r) => r.meta.duration_ms - offset(r)),
	);
	$("scrub").max = state.end;
	renderChoices();
	const all = [...state.chosen.values()].filter((r) => r.summary),
		signatures = new Set(
			all.map((r) =>
				JSON.stringify([
					r.meta.manifest.scenario,
					r.meta.manifest.initial_sha256,
					r.meta.manifest.memory_mode,
				]),
			),
		);
	say(
		all.length
			? `${all.some((r) => r.meta.incomplete || r.summary.metrics.gaps) ? "Há lacunas registradas. " : ""}${all.some((r) => r.meta.manifest.synthetic) ? "Dados simulados não medem desempenho real. " : ""}${signatures.size > 1 || all.some((r) => !r.meta.manifest.initial_sha256) ? "Comparação descritiva: condições iniciais não verificadas como equivalentes." : "Condições iniciais identificadas por hash; resultados descritivos, sem vencedor automático."} Mapas e curvas usam amostras; o inspetor busca o estado registrado no instante selecionado.`
			: "Selecione uma gravação para começar.",
	);
	draw();
}
function nearest(track, t) {
	let low = 0,
		high = track.length;
	while (low < high) {
		let mid = (low + high) >> 1;
		if (track[mid].t_ms <= t) low = mid + 1;
		else high = mid;
	}
	return track[low - 1] || null;
}
function drawMap(r, t) {
	const canvas = r.node.querySelector(".map"),
		c = canvas.getContext("2d"),
		tracked = nearest(r.track, t),
		sample =
			r.sample &&
			r.sample.t_ms <= t &&
			(!tracked || r.sample.t_ms >= tracked.t_ms)
				? r.sample
				: tracked;
	c.clearRect(0, 0, 700, 420);
	if (!sample) {
		c.fillStyle = "#9eafb4";
		c.fillText("Sem observação neste instante", 25, 40);
		return;
	}
	const b = sample.data.bot,
		floor = b.position[2],
		points = r.track.filter(
			(e) => e.t_ms <= t && e.data.bot.position[2] === floor,
		);
	r.node.querySelector(".floor").textContent = `andar ${floor}`;
	const xs = points.map((p) => p.data.bot.position[0]).concat(b.position[0]),
		ys = points.map((p) => p.data.bot.position[1]).concat(b.position[1]);
	let minX = Math.min(...xs) - 6,
		minY = Math.min(...ys) - 6,
		maxX = Math.max(...xs) + 6,
		maxY = Math.max(...ys) + 6;
	const scale = Math.min(640 / (maxX - minX), 350 / (maxY - minY)),
		px = (x) => 30 + (x - minX) * scale,
		py = (y) => 25 + (y - minY) * scale;
	c.strokeStyle = "#223239";
	c.lineWidth = 1;
	const step = Math.max(1, Math.ceil(15 / scale));
	for (let x = Math.ceil(minX / step) * step; x <= maxX; x += step) {
		c.beginPath();
		c.moveTo(px(x), 20);
		c.lineTo(px(x), 390);
		c.stroke();
	}
	for (let y = Math.ceil(minY / step) * step; y <= maxY; y += step) {
		c.beginPath();
		c.moveTo(20, py(y));
		c.lineTo(680, py(y));
		c.stroke();
	}
	c.strokeStyle = r.color;
	c.lineWidth = 2;
	c.setLineDash([4, 5]);
	c.beginPath();
	let prev = null;
	for (const p of points) {
		const pos = p.data.bot.position;
		if (
			!prev ||
			(r.summary.metrics.gap_times || []).some(
				(g) => g > prev.t_ms && g <= p.t_ms,
			)
		)
			c.moveTo(px(pos[0]), py(pos[1]));
		else c.lineTo(px(pos[0]), py(pos[1]));
		prev = p;
	}
	c.stroke();
	c.setLineDash([]);
	c.fillStyle = r.color;
	c.beginPath();
	c.arc(px(b.position[0]), py(b.position[1]), 6, 0, 2 * Math.PI);
	c.fill();
	r.node.querySelector(".position").textContent =
		`${clock(t)} · (${b.position.join(", ")}) · nível ${b.level} · XP ${fmt(b.xp)} · HP ${b.health}% · ${b.objective} · amostra ${clock(sample.t_ms)}`;
}
function drawChart(r, t) {
	const c = r.node.querySelector(".chart").getContext("2d");
	c.clearRect(0, 0, 700, 120);
	if (!r.track.length) return;
	const xp = r.track.map((e) => e.data.bot.xp),
		lo = Math.min(...xp),
		hi = Math.max(...xp),
		span = Math.max(1, hi - lo);
	c.strokeStyle = r.color;
	c.lineWidth = 2;
	c.beginPath();
	for (let i = 0; i < r.track.length; i++) {
		const p = r.track[i],
			x = 20 + (p.t_ms / Math.max(1, r.meta.duration_ms)) * 660,
			y = 98 - ((p.data.bot.xp - lo) / span) * 76;
		if (
			!i ||
			(r.summary.metrics.gap_times || []).some(
				(g) => g > r.track[i - 1].t_ms && g <= p.t_ms,
			)
		)
			c.moveTo(x, y);
		else c.lineTo(x, y);
	}
	c.stroke();
	c.strokeStyle = "#ffffff88";
	c.beginPath();
	const x = 20 + (t / Math.max(1, r.meta.duration_ms)) * 660;
	c.moveTo(x, 10);
	c.lineTo(x, 110);
	c.stroke();
}
function draw() {
	$("scrub").value = state.time;
	$("clock").textContent = clock(state.time);
	for (const r of state.chosen.values())
		if (r.node) {
			drawMap(r, timeFor(r));
			drawChart(r, timeFor(r));
		}
}
async function inspect() {
	const generation = ++state.request;
	for (const r of state.chosen.values()) {
		if (!r.node) continue;
		const t = timeFor(r);
		try {
			const [seek, events] = await Promise.all([
				api("replay/seek", { run: r.meta.id, at: Math.floor(t) }),
				api("replay/timeline", { run: r.meta.id, at: Math.floor(t) }),
			]);
			if (generation !== state.request) return;
			r.sample = seek.sample;
			const target = r.node.querySelector(".timeline");
			target.replaceChildren();
			for (const event of events.slice(0, 40)) {
				const item = document.createElement("details");
				item.className = "event";
				const heading = document.createElement("summary");
				heading.textContent = `${clock(event.t_ms)} · ${labels[event.kind] || event.kind} · ${event.data.phase || event.data.status || event.data.kind || ""}`;
				const data = document.createElement("pre");
				data.textContent = JSON.stringify(event.data, null, 2);
				item.append(heading, data);
				target.append(item);
			}
			draw();
		} catch (e) {
			say(e.message);
		}
	}
}
function jump(t) {
	state.time = Math.min(state.end, Math.max(0, +t));
	for (const r of state.chosen.values()) r.sample = null;
	draw();
	inspect();
}
$("play").addEventListener("click", () => {
	state.playing = !state.playing;
	$("play").textContent = state.playing ? "Ⅱ Pausar" : "▶ Reproduzir";
	state.last = performance.now();
});
$("scrub").addEventListener("input", (e) => jump(e.target.value));
$("alignment").addEventListener("change", () => {
	layout();
	jump(0);
});
let inspected = 0;
function frame(now) {
	if (state.playing) {
		state.time = Math.min(
			state.end,
			state.time + (now - state.last) * +$("speed").value,
		);
		if (state.time === state.end) {
			state.playing = false;
			$("play").textContent = "▶ Reproduzir";
		}
		draw();
		if (!state.playing || now - inspected > 700) {
			inspect();
			inspected = now;
		}
	}
	state.last = now;
	requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
async function refresh() {
	try {
		state.runs = await api("replays");
		renderChoices();
		if (!state.runs.length)
			say(
				"Ainda não há jornadas gravadas. Habilite a gravação no worker ou importe um arquivo de replay.",
			);
		else if (!state.chosen.size) await select(state.runs[0], true);
	} catch (e) {
		say(e.message);
	}
}
$("refresh").addEventListener("click", refresh);
refresh();
